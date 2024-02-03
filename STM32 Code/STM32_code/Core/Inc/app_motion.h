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
#include "pid.h"
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
	bool _setDutyCycleVal(uint32_t dc);
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
	Encoder(TIM_HandleTypeDef *ctrl, uint32_t channel);
	~Encoder() {};
	uint32_t getCount();
	uint32_t getDelta(uint32_t ct1, uint32_t ct2);

private:
	TIM_HandleTypeDef *htimer;
		uint32_t channel;

};

class MotionController {

#define CENTER_POS_PWM 148 //150
#define LEFT_DELTA 50  // was 40
#define RIGHT_DELTA 100 // was 80 then 100

#define LEFT_POS_PWM (CENTER_POS_PWM - RIGHT_DELTA)
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
	void move(bool isFwd, uint32_t arg, uint32_t speed);
	void emergencyStop();
	~MotionController() {
	}
	;
	u_ctx *ctx;
	static void motionTask(void *pv);
	static float map(float x, float in_min, float in_max, float out_min, float out_max) {
	    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
	}
private:
	Motor *lmotor;
	Motor *rmotor;
	Servo *servo;
	Encoder *lencoder;
	Encoder *rencoder;
	pid_type_def left_pid, right_pid;
	pid_type_def sync_left_pid, sync_right_pid;
	bool emergency;
};

}

#endif /* INC_APP_MOTION_H_ */
