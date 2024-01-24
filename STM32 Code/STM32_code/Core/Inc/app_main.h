/*
 * app_main.h
 *
 *  Created on: Jan 22, 2024
 *      Author: edward62740
 */

#ifndef INC_APP_MAIN_H_
#define INC_APP_MAIN_H_

#ifdef __cplusplus
extern "C" {
#endif
#include "cmsis_os2.h"

void sensorTask(void *pv);
void UARTReceiveTask(void const * argument);
void initializeCPPconstructs(void);

void processorTask(void const *);

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif /* INC_APP_MAIN_H_ */
