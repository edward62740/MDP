/*
 * app_motion.h
 *
 *  Created on: Jan 22, 2024
 *      Author: edward62740
 */

#ifndef INC_APP_MOTION_H_
#define INC_APP_MOTION_H_

#include "cmsis_os2.h"
#include "stm32f4xx_hal.h"
#include "app_parser.h"

namespace AppMotion { // application-layer motion logic
/* Servo class that holds servo info */
class Servo {
public:

	Servo(TIM_HandleTypeDef *ctrl, uint32_t channel, uint32_t min, uint32_t max,
			uint32_t center);
	~Servo() {
	}
	;
	void turnLeft();
	void turnRight();
	void turnFront();
	void turnToPos(uint32_t count);
	static const uint32_t TURN_DELAY_MS = 250UL;
private:
	TIM_HandleTypeDef *htimer;
	uint32_t channel;
	uint32_t state;
	uint32_t MIN_PWM;
	uint32_t MAX_PWM;
	uint32_t CTR_PWM;

};
/* Motor class that holds motor info */
class Motor {
public:
	Motor(TIM_HandleTypeDef *ctrl, uint32_t channel, GPIO_TypeDef *gpioAPort,
			GPIO_TypeDef *gpioBPort, uint16_t gpioApin, uint16_t gpioBpin,
			uint32_t pwm_period = 7199);
	~Motor() {
	}
	;
	bool setSpeed(uint32_t percent);
	void setForward(void);
	void setBackward(void);
	void halt(void);

private:
	TIM_HandleTypeDef *htimer;
	uint32_t channel;
	uint32_t period;
	GPIO_TypeDef *gpioAPort;
	GPIO_TypeDef *gpioBPort;
	uint16_t gpioAPin;
	uint16_t gpioBpin;

};

class Encoder {
public:

};

class MotionController {

#define CENTER_POS_PWM 153 //150
#define LEFT_DELTA 40  // was 40
#define RIGHT_DELTA 90 // was 80 then 100

#define LEFT_POS_PWM (CENTER_POS_PWM - LEFT_DELTA)
#define RIGHT_POS_PWM (CENTER_POS_PWM + RIGHT_DELTA)
	typedef struct {
	    u_ctx* ctx;
	    MotionController* i;
	} instance_wrapper; // for passing to class instance info to static task fn, workaround.


public:

	MotionController(u_ctx *ctx);

	void start();
	void turn(bool isRight, bool isFwd,
			uint32_t arg);
	void emergencyStop();
	~MotionController() {
	}
	;
	u_ctx *ctx;
	static void motionTask(void *pv);
private:
	Motor *lmotor;
	Motor *rmotor;
	Servo *servo;
};

}

#endif /* INC_APP_MOTION_H_ */
