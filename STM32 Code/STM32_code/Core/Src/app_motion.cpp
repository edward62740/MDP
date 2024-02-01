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
#include "pid.h"
#include "oled.h"//remove
#include <cstdlib>
#include <cstdio>
#include <cstring>

namespace AppMotion {

#define ALPHA 0.8
#define REAR_WHEEL_RADIUS_CM 6.5/2
#define REAR_WHEEL_ROTATION_DISTANCE (2 * 3.142 * REAR_WHEEL_RADIUS_CM)
#define ENCODER_PULSES_PER_ROTATION 1560
#define DISTANCE_PER_ENCODER_PULSE (REAR_WHEEL_ROTATION_DISTANCE / ENCODER_PULSES_PER_ROTATION)

MotionController::MotionController(u_ctx *ctx) {
	this->ctx = ctx;
	/* Instantiate the physical devices */

}

void MotionController::start(void) {
	this->servo = new Servo(&htim1, TIM_CHANNEL_1, CENTER_POS_PWM - LEFT_DELTA,
	CENTER_POS_PWM + RIGHT_DELTA, CENTER_POS_PWM);
	this->lmotor = new Motor(&htim8, TIM_CHANNEL_1, GPIOA, GPIOA, GPIO_PIN_5,
	GPIO_PIN_4, 7199);
	this->rmotor = new Motor(&htim8, TIM_CHANNEL_2, GPIOA, GPIOA, GPIO_PIN_2,
	GPIO_PIN_3, 7199);
	float pid_param_right[3] = { 3.1, 0.0, 0.1 };
	PID_init(&this->left_pid, PID_POSITION, pid_param_right, 4000, 3000);
	PID_init(&this->right_pid, PID_POSITION, pid_param_right, 4000, 3000);

	this->lencoder = new Encoder(&htim2, TIM_CHANNEL_ALL);
	this->rencoder = new Encoder(&htim3, TIM_CHANNEL_ALL);
	emergency = false;
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
	osDelay(4500);
	servo->turnLeft();
		servo->turnRight();
		servo->turnFront();

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

				self->move(true, pkt.arg, 15);

			} else if (pkt.cmd == AppParser::MOTION_CMD::MOVE_BWD) {
				servo->turnFront();

				self->move(false, pkt.arg, 15);

			} else if (pkt.cmd == AppParser::MOTION_CMD::MOVE_LEFT_FWD) {
				self->turn(false, true, pkt.arg);

			} else if (pkt.cmd == AppParser::MOTION_CMD::MOVE_RIGHT_FWD)
				self->turn(true, true, pkt.arg);

			else if (pkt.cmd == AppParser::MOTION_CMD::MOVE_LEFT_BWD) {
				self->turn(false, false, pkt.arg);

			} else if (pkt.cmd == AppParser::MOTION_CMD::MOVE_RIGHT_BWD)
				self->turn(true, false, pkt.arg);
		}
		HAL_GPIO_TogglePin(GPIOE, GPIO_PIN_10);

	}
}


void MotionController::move(bool isFwd, uint32_t arg, uint32_t speed) {
	emergency = false;
	servo->turnFront();
	isFwd ? lmotor->setForward() : lmotor->setBackward();
	isFwd ? rmotor->setForward() : rmotor->setBackward();
	lmotor->setSpeed(speed);
	rmotor->setSpeed(speed);
	uint32_t timeStart = HAL_GetTick();
	uint32_t l_encoder_count = lencoder->getCount();
	uint32_t r_encoder_count = rencoder->getCount();
	double target = (double) arg / DISTANCE_PER_ENCODER_PULSE;

	double cur_left = 0, cur_right = 0;
	float count_left = 0, count_right = 0;
	do {
		if (cur_left > target - 2000 || cur_right > target - 2000) {
			lmotor->setSpeed(map(target - cur_left, 2000, 330, 20, 8));
			rmotor->setSpeed(map(target - cur_right, 2000, 330, 20, 8));
		} else {
			lmotor->_setDutyCycleVal(
					PID_calc(&this->left_pid, cur_left, target));
			rmotor->_setDutyCycleVal(
					PID_calc(&this->right_pid, cur_right, target));
		}
		/*
		cur_left += DISTANCE_PER_ENCODER_PULSE
				* abs(
						(float) lencoder->getDelta(l_encoder_count,
								lencoder->getCount()));
		cur_right += DISTANCE_PER_ENCODER_PULSE
				* abs(
						(float) rencoder->getDelta(r_encoder_count,
								rencoder->getCount()));
								*/
		l_encoder_count = lencoder->getCount();
		r_encoder_count = rencoder->getCount();

		if (cur_left > target || cur_right > target || emergency)
			break;

		osDelay(50);
		cur_left += (double) lencoder->getDelta(l_encoder_count,
				lencoder->getCount());
		cur_right += (double) rencoder->getDelta(r_encoder_count,
				rencoder->getCount());
		//osThreadYield();

	} while (1);
	emergency = false;
	lmotor->halt();
	rmotor->halt();
}

void MotionController::turn(bool isRight, bool isFwd, uint32_t arg) {
	emergency = false;
	isRight ? servo->turnRight() : servo->turnLeft();

	isFwd ? lmotor->setForward() : lmotor->setBackward();
	isFwd ? rmotor->setForward() : rmotor->setBackward();
	isRight ? lmotor->setSpeed(30) : lmotor->setSpeed(0);
	isRight ? rmotor->setSpeed(0) : rmotor->setSpeed(30);
	uint32_t timeNow = HAL_GetTick();
	uint32_t timeStart = timeNow;
	uint8_t buf[30] = { 0 };
	float target_yaw = 0;
	float req = (float) arg;
	float cur = sensor_data.yaw_abs; //[-179,180]
	float prev_yaw = cur;

	if((!isRight && isFwd) || (isRight && !isFwd) )
	{
		if((req + cur) > 179) target_yaw = -180 + (req - (180 - cur));
		else target_yaw = req + cur;
	}
	else
	{
		if((cur + -1*req) < -179) target_yaw = 180 - (req + (-180 - cur));
		else target_yaw = cur - req;
	}

	do{
		if (abs(target_yaw - cur) < 29) {
			if(isRight) lmotor->setSpeed((uint32_t)map(abs(target_yaw - cur), 29, 0, 30, 15));

			else rmotor->setSpeed((uint32_t)map(abs(target_yaw - cur), 29, 0, 30, 15));
		}

		timeNow = HAL_GetTick();
		cur = 0.1*sensor_data.yaw_abs + 0.9*prev_yaw; //filter
		prev_yaw = cur;

		if (abs(cur - target_yaw) < 3
				|| (HAL_GetTick() - timeStart) > 10000 || emergency)
			break;

		osDelay(2);
		osThreadYield(); // need to ensure yield for the sensortask

	} while (1);

	emergency = false;
	lmotor->halt();
	rmotor->halt();
}

void MotionController::emergencyStop() {
	emergency = true;
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

bool Motor::_setDutyCycleVal(uint32_t dc) {
	if (dc > this->period)
		return false;
		__HAL_TIM_SET_COMPARE(this->htimer, this->channel, dc);
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

Encoder::Encoder(TIM_HandleTypeDef *ctrl, uint32_t channel) {

	this->htimer = ctrl;
	this->channel = channel;
	HAL_TIM_Encoder_Start(ctrl, channel);

}

uint32_t Encoder::getCount(void) {
	return (uint32_t) __HAL_TIM_GET_COUNTER(this->htimer);
}

uint32_t Encoder::getDelta(uint32_t ct1, uint32_t ct2) {
	if (__HAL_TIM_IS_TIM_COUNTING_DOWN(this->htimer)) {
		if (ct2 <= ct1) {
			return ct1 - ct2;
		} else {
			return (65535 - ct2) + ct1;
		}
	} else {
		if (ct2 >= ct1) {
			return ct2 - ct1;
		} else {
			return (65535 - ct1) + ct2;
		}
	}
}

}
