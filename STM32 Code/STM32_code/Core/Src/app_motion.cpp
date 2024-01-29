/*
 * app_motion.cpp
 *
 * Functions to control motion
 *
 *  Created on: Jan 22, 2024
 *      Author: edward62740
 *
 */
#include "app_motion.h"
#include "stm32f4xx_hal.h"
#include "cmsis_os2.h"
#include "main.h"
#include "app_main.h"
#include <cstdlib>
#include <cstdio>
#include <cstring>

namespace AppMotion {

MotionController::MotionController(u_ctx *ctx) {
	this->ctx = ctx;
	/* Instantiate the physical devices */

	this->servo = new Servo(&htim1, TIM_CHANNEL_1, CENTER_POS_PWM - LEFT_DELTA,
			CENTER_POS_PWM + RIGHT_DELTA, CENTER_POS_PWM);
	this->lmotor = new Motor(&htim8, TIM_CHANNEL_1, GPIOA, GPIOA, GPIO_PIN_5, GPIO_PIN_4,
			7199);
	this->rmotor = new Motor(&htim8, TIM_CHANNEL_2, GPIOA, GPIOA, GPIO_PIN_2, GPIO_PIN_3,
			7199);

}

void MotionController::start(void) {


	instance_wrapper *wrapper_instance = new instance_wrapper();
	wrapper_instance->ctx = ctx;
	wrapper_instance->i = this;
	this->ctx->runner = osThreadNew(
			(osThreadFunc_t) MotionController::motionTask, wrapper_instance,
			&(ctx->attr));
	return;
}

void MotionController::motionTask(void *pv) {

	// workaround section START
	instance_wrapper *wrapper = static_cast<instance_wrapper*>(pv);
	u_ctx *ctx = wrapper->ctx;
	MotionController *self = wrapper->i;

	Motor *lmotor = self->lmotor;
	Motor *rmotor = self->rmotor;
	Servo *servo = self->servo;

	/* workaround section END. henceforth refer to any "this" as "self" */
	for (;;) {
		osDelay(50);
		is_task_alive_struct.motn = true;

		//osThreadYield();
		if (osMessageQueueGetCount(ctx->mailbox.queue) > 0) {
			AppParser::MOTION_PKT_t pkt;
			osMessageQueueGet(ctx->mailbox.queue, &pkt, 0, 5);
			char buffer[20] = { 0 };
			sprintf((char*) &buffer, "cmd:%ld, arg:%ld\r\n", (uint32_t) pkt.cmd,
					pkt.arg);
			//HAL_UART_Transmit(&huart3, (uint8_t*) buffer, sizeof(buffer), 10);
			if (pkt.cmd == AppParser::MOTION_CMD::MOVE_FWD) {
				servo->turnFront();
				lmotor->setSpeed(30);
				rmotor->setSpeed(30);
				lmotor->setForward();
				rmotor->setForward();
				osDelay(500); // replace delay with tachometer count down
				lmotor->halt();
				rmotor->halt();
			} else if (pkt.cmd == AppParser::MOTION_CMD::MOVE_LEFT_FWD) {
				self->turn(false, true, pkt.arg);

			} else if (pkt.cmd == AppParser::MOTION_CMD::MOVE_RIGHT_FWD)
				self->turn(true, true, pkt.arg);
		}
		HAL_GPIO_TogglePin(GPIOE, GPIO_PIN_10);

	}
}

void MotionController::turn(bool isRight, bool isFwd, uint32_t arg) {
	isRight ? servo->turnRight() : servo->turnLeft();

	isFwd ? lmotor->setForward() : lmotor->setBackward();
	isFwd ? rmotor->setForward() : rmotor->setBackward();
	isRight ? lmotor->setSpeed(50) : lmotor->setSpeed(10);
	isRight ? rmotor->setSpeed(10) : rmotor->setSpeed(50);
	uint32_t timeNow = HAL_GetTick();
	uint8_t buf[30] = { 0 };
	float target = (float) arg;
	float angle = 0;
	do { // TODO CHANGE TO QUATERNION YAW

		angle += sensor_data.imu->gyro[2] * (HAL_GetTick() - timeNow) * 0.001;
		if ((!isRight && isFwd && angle > target)
				|| (isRight && isFwd && angle < -target)
				|| (!isRight && !isFwd && angle < -target)
				|| (isRight && !isFwd && angle > target))
			break;
		timeNow = HAL_GetTick();
		osDelay(50);
		osThreadYield();

	} while (1);

	lmotor->halt();
	rmotor->halt();
}

void MotionController::emergencyStop() {
	lmotor->halt();
	rmotor->halt();
}

Servo::Servo(TIM_HandleTypeDef *ctrl, uint32_t channel, uint32_t min,
		uint32_t max, uint32_t center) {
	this->htimer = ctrl;
	this->channel = channel;
	this->MIN_PWM = min;
	this->MAX_PWM = max;
	this->CTR_PWM = center;
	HAL_TIM_PWM_Start(ctrl, channel);
}

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

Motor::Motor(TIM_HandleTypeDef *ctrl, uint32_t channel, GPIO_TypeDef *gpioAPort,
		GPIO_TypeDef *gpioBPort, uint16_t gpioApin, uint16_t gpioBpin,
		uint32_t pwm_period) {

	this->htimer = ctrl;
	this->channel = channel;
	this->period = pwm_period;
	this->gpioAPort = gpioAPort;
	this->gpioBPort = gpioBPort;
	this->gpioAPin = gpioApin;
	this->gpioBpin = gpioBpin;
	HAL_TIM_PWM_Start(ctrl, channel);

}

bool Motor::setSpeed(uint32_t percent) {
	if (percent > 100)
		return false;
	uint32_t value = this->period / 100 * percent;
	__HAL_TIM_SET_COMPARE(this->htimer, this->channel, value);
	return true;
}

void Motor::halt() {
	__HAL_TIM_SET_COMPARE(this->htimer, this->channel, 0);
}

void Motor::setForward() {
	HAL_GPIO_WritePin(this->gpioAPort, this->gpioAPin, GPIO_PIN_RESET);
	HAL_GPIO_WritePin(this->gpioBPort, this->gpioBpin, GPIO_PIN_SET);
}

void Motor::setBackward() {
	HAL_GPIO_WritePin(this->gpioAPort, this->gpioAPin, GPIO_PIN_SET);
	HAL_GPIO_WritePin(this->gpioBPort, this->gpioBpin, GPIO_PIN_RESET);
}

}
