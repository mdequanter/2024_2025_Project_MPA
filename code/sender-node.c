#include "contiki.h"
#include "lib/random.h"
#include "sys/ctimer.h"
#include "sys/etimer.h"
#include "net/ipv6/uip.h"
#include "net/ipv6/uip-ds6.h"
#include "net/ipv6/uip-debug.h"
#include "simple-udp.h"

#include <stdio.h>
#include <string.h>

#define UDP_PORT 1234

//#define SEND_INTERVAL    (60 * CLOCK_SECOND / 10)
#define SEND_INTERVAL    ((10 * CLOCK_SECOND))
#define START_DELAY      (CLOCK_SECOND * 600)
#define JITTER_PERCENT   100

static struct simple_udp_connection unicast_connection;

/*---------------------------------------------------------------------------*/
// Jittered interval generator: ±20% of base
static clock_time_t get_jittered_interval(clock_time_t base) {
  uint16_t jitter_range = (base * JITTER_PERCENT) / 100;
  int16_t jitter = (random_rand() % (2 * jitter_range + 1)) - jitter_range;
  return base + jitter;
}
/*---------------------------------------------------------------------------*/
PROCESS(sender_node_process, "Sender node process");
AUTOSTART_PROCESSES(&sender_node_process);
/*---------------------------------------------------------------------------*/
static void
receiver(struct simple_udp_connection *c,
         const uip_ipaddr_t *sender_addr,
         uint16_t sender_port,
         const uip_ipaddr_t *receiver_addr,
         uint16_t receiver_port,
         const uint8_t *data,
         uint16_t datalen)
{
  printf("Sender received data on port %d from port %d with length %d\n",
         receiver_port, sender_port, datalen);
}
/*---------------------------------------------------------------------------*/
static void
set_global_address(void)
{
  uip_ipaddr_t ipaddr;
  int i;
  uint8_t state;
  const uip_ipaddr_t *default_prefix = uip_ds6_default_prefix();

  uip_ip6addr_copy(&ipaddr, default_prefix);
  uip_ds6_set_addr_iid(&ipaddr, &uip_lladdr);
  uip_ds6_addr_add(&ipaddr, 0, ADDR_AUTOCONF);

  printf("IPv6 addresses: ");
  for(i = 0; i < UIP_DS6_ADDR_NB; i++) {
    state = uip_ds6_if.addr_list[i].state;
    if(uip_ds6_if.addr_list[i].isused &&
       (state == ADDR_TENTATIVE || state == ADDR_PREFERRED)) {
      uip_debug_ipaddr_print(&uip_ds6_if.addr_list[i].ipaddr);
      printf("\n");
    }
  }
}
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(sender_node_process, ev, data)
{
  static struct etimer periodic_timer;
  static struct etimer start_timer;

  uip_ipaddr_t addr;
  const uip_ipaddr_t *default_prefix;

  PROCESS_BEGIN();

  set_global_address();

  simple_udp_register(&unicast_connection, UDP_PORT, NULL, UDP_PORT, receiver);

  etimer_set(&start_timer, START_DELAY);
  PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&start_timer));
  printf("START SENDING TIMER %ld EXPIRED\n", START_DELAY);

  static unsigned int message_number = 0;

  while(1) {
    clock_time_t jittered_interval = get_jittered_interval(SEND_INTERVAL);
    etimer_set(&periodic_timer, jittered_interval);
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&periodic_timer));

    if(message_number >= 100) {
      printf("All messages send\n");
      continue;
    }

    default_prefix = uip_ds6_default_prefix();
    uip_ip6addr_copy(&addr, default_prefix);
    addr.u16[4] = UIP_HTONS(0x0210);
    addr.u16[5] = UIP_HTONS(0x0010);
    addr.u16[6] = UIP_HTONS(0x0010);
    addr.u16[7] = UIP_HTONS(0x0010);

    char buf[80];
    char ipbuf[40];
    uip_ipaddr_t *my_ip = NULL;

    for(int i = 0; i < UIP_DS6_ADDR_NB; i++) {
      if(uip_ds6_if.addr_list[i].isused &&
         uip_ds6_if.addr_list[i].state == ADDR_PREFERRED) {
        my_ip = &uip_ds6_if.addr_list[i].ipaddr;
        break;
      }
    }

    if(my_ip != NULL) {
      uiplib_ipaddr_snprint(ipbuf, sizeof(ipbuf), my_ip);
      snprintf(buf, sizeof(buf), "Msg %s %d", ipbuf, message_number);
    } else {
      snprintf(buf, sizeof(buf), "Msg unknown %d", message_number);
    }

    printf("Sending message: '%s' to ", buf);
    uip_debug_ipaddr_print(&addr);
    printf("\n");
    simple_udp_sendto(&unicast_connection, buf, strlen(buf) + 1, &addr);
    message_number++;
  }

  PROCESS_END();
}
/*---------------------------------------------------------------------------*/
