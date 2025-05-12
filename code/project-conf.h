/*
 * Copyright (c) 2016, Inria.
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





 
#define TCPIP_CONF_ANNOTATE_TRANSMISSIONS 1
#define LOG_CONF_LEVEL_RPL LOG_LEVEL_DBG

//#define TSCH_JOIN_HOPPING_SEQUENCE_2_2

#define LOG_CONF_LEVEL_MAC LOG_LEVEL_DBG
//#define LOG_CONF_LEVEL_MAC LOG_LEVEL_DBG

//#define TSCH_SCHEDULE_CONF_WITH_ORCHESTRA 1

// changed from 8 to 16,  because we need to send more packets
//#define TSCH_QUEUE_CONF_MAX_PACKETS_PER_NEIGHBOR 16

// because of RAM memory constraints we cannot put this higher. We assume with 64 that we have 256KB RAM, like a nRF52840
#define QUEUEBUF_CONF_NUM 64


// Lower unicast slotframe lenght (standard  17)
//#define ORCHESTRA_CONF_UNICAST_PERIOD 7


#define LOG_CONF_LEVEL_ORCHESTRA LOG_LEVEL_DBG