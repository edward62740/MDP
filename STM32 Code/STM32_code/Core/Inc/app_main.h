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
#include "ICM20948.h"

void sensorTask(void *pv);
void UARTReceiveTask(void const * argument);
void initializeCPPconstructs(void);
extern bool test_run;
typedef struct {
	ICM20948 *imu;
	float ir_distL;
	float ir_distR;
	float usonic_dist;
	uint32_t d_valid; // bitwise data valid mask. starts with LSB.

} sensorData_t;

const uint32_t AC_VALID_MASK = 0x1;
const uint32_t GY_VALID_MASK = 0x2;
const uint32_t MG_VALID_MASK = 0x4;
const uint32_t TM_VALID_MASK = 0x8;
const uint32_t IR_L_VALID_MASK = 0x10;
const uint32_t IR_R_VALID_MASK = 0x20;
const uint32_t USONIC_VALID_MASK = 0x40;
extern sensorData_t sensor_data;

void processorTask(void const *);

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif /* INC_APP_MAIN_H_ */
