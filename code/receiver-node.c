/*
 * Copyright (c) 2012, Thingsquare, www.thingsquare.com.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the Institute nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE INSTITUTE AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE INSTITUTE OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 */

 #include "contiki.h"
 #include "lib/random.h"
 #include "sys/ctimer.h"
 #include "sys/etimer.h"
 #include "net/ipv6/uip.h"
 #include "net/ipv6/uip-ds6.h"
 #include "net/ipv6/uip-ds6-route.h"
 #include "net/ipv6/uip-debug.h"
 
 #include "simple-udp.h"
 
 #include "net/routing/routing.h"
 #include "dev/leds.h"
 
 #include <stdio.h>
 #include <string.h>
 
 #define UDP_PORT 1234
 
 static struct simple_udp_connection unicast_connection;

 uint32_t hops;
 
 /*---------------------------------------------------------------------------*/
 PROCESS(receiver_node_process, "Receiver node");
 AUTOSTART_PROCESSES(&receiver_node_process);
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

  hops = uip_ds6_if.cur_hop_limit - UIP_IP_BUF->ttl + 1;
  printf("Received %d hops\n", hops);
  
  printf("Data received from ");
  uip_debug_ipaddr_print(sender_addr);
  
  // Zorg ervoor dat we het als string kunnen afdrukken
  char msg[datalen + 1];
  memcpy(msg, data, datalen);
  msg[datalen] = '\0';  // Zorg voor null-terminatie
  
  printf(" on port %d from port %d in %d hops with datalength %d: '%s'\n",
         receiver_port, sender_port,hops, datalen, msg);
 }
 /*---------------------------------------------------------------------------*/
 static uip_ipaddr_t *
 set_global_address(void)
 {
   static uip_ipaddr_t ipaddr;
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
 
   return &ipaddr;
 }
 /*---------------------------------------------------------------------------*/
 #if RPL_WITH_STORING
 uint8_t should_blink = 1;
 static void
 route_callback(int event, const uip_ipaddr_t *route, const uip_ipaddr_t *ipaddr, int num_routes)
 {
   if(event == UIP_DS6_NOTIFICATION_DEFRT_ADD) {
     should_blink = 0;
   } else if(event == UIP_DS6_NOTIFICATION_DEFRT_RM) {
     should_blink = 1;
   }
 }
 #endif /* #if RPL_WITH_STORING */
 /*---------------------------------------------------------------------------*/
 PROCESS_THREAD(receiver_node_process, ev, data)
 {
   static struct etimer et;
 #if RPL_WITH_STORING
   static struct uip_ds6_notification n;
 #endif /* #if RPL_WITH_STORING */
 
   PROCESS_BEGIN();
 
   set_global_address();
 
 #if RPL_WITH_STORING
   uip_ds6_notification_add(&n, route_callback);
 #endif /* #if RPL_WITH_STORING */
 
   simple_udp_register(&unicast_connection, UDP_PORT,
                       NULL, UDP_PORT, receiver);
 
   etimer_set(&et, CLOCK_SECOND);
   while(1) {
     PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&et));
     etimer_reset(&et);
 #if RPL_WITH_STORING
     if(should_blink) {
       //leds_on(LEDS_ALL);
       PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&et));
       etimer_reset(&et);
       //leds_off(LEDS_ALL);
     }
 #endif /* #if RPL_WITH_STORING */
   }
   PROCESS_END();
 }
 /*---------------------------------------------------------------------------*/