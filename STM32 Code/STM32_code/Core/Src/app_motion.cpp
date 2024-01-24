/*
 * app_motion.cpp
 *
 * Functions to control motion
 *
 *  Created on: Jan 22, 2024
 *      Author: eward62740
 *
 */
#include "app_motion.h"
#include "stm32f4xx_hal.h"
#include "cmsis_os2.h"
#include "main.h"
#include <cstdlib>
#include <cstdio>
#include <cstring>


namespace AppMotion {

MotionController::MotionController(u_ctx *ctx) {
	this->ctx = ctx;

}
MotionController::~MotionController() {
}
;
void MotionController::start(void) {

	this->ctx->runner = osThreadNew((osThreadFunc_t) &MotionController::motionTask, ctx,
			&(ctx->attr));
}

void MotionController::motionTask(void *pv) {
	u_ctx *ctx = (u_ctx*) pv;
	Servo servo(&htim1, CENTER_POS_PWM - LEFT_DELTA,
			CENTER_POS_PWM + RIGHT_DELTA, CENTER_POS_PWM);
	//for (;;) {
		//osDelay(50);
		//osThreadYield();
		if (osMessageQueueGetCount(ctx->mailbox.queue) > 0) {
			AppParser::MOTION_PKT_t pkt;
			osMessageQueueGet(ctx->mailbox.queue, &pkt, 0, 5);
			char buffer[20] = { 0 };
			sprintf((char*) &buffer, "cmd:%ld, arg:%ld\r\n",
					(uint32_t) pkt.cmd, pkt.arg);
			HAL_UART_Transmit(&huart3, (uint8_t*) buffer, sizeof(buffer), 10);
			if(pkt.cmd == AppParser::MOTION_CMD::MOVE_FWD) servo.turnFront();
			else if(pkt.cmd == AppParser::MOTION_CMD::MOVE_LEFT_BWD) servo.turnLeft();
			else if(pkt.cmd == AppParser::MOTION_CMD::MOVE_RIGHT_BWD) servo.turnRight();
		}
		//HAL_GPIO_TogglePin(GPIOE, GPIO_PIN_10);

	//}
}

Servo::Servo(TIM_HandleTypeDef *ctrl, uint32_t min, uint32_t max,
		uint32_t center) {
	this->htimer = ctrl;
	this->MIN_PWM = min;
	this->MAX_PWM = max;
	this->CTR_PWM = center;
	HAL_TIM_PWM_Start(ctrl, TIM_CHANNEL_1);
}
Servo::~Servo(){};
void Servo::turnLeft() {
	this->htimer->Instance->CCR1 = MIN_PWM;
	osDelay(TURN_DELAY_MS);

}
void Servo::turnRight() {
	this->htimer->Instance->CCR1 = MAX_PWM;
	osDelay(TURN_DELAY_MS);
}

void Servo::turnFront() {
	this->htimer->Instance->CCR1 = CTR_PWM;
	osDelay(TURN_DELAY_MS);
}
/*
 void MotionController::setLeftPWM(uint16_t dutyCycle) {
 __HAL_TIM_SET_COMPARE(&htim8, TIM_CHANNEL_1, dutyCycle);
 }

 void MotionController::setRightPWM(uint16_t dutyCycle) {
 __HAL_TIM_SET_COMPARE(&htim8, TIM_CHANNEL_2, dutyCycle);
 }
 */

}
