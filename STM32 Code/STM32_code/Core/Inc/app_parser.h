/*
 * app_parser.h
 *
 *  Created on: Jan 22, 2024
 *      Author: edward62740
 */

#ifndef INC_APP_PARSER_H_
#define INC_APP_PARSER_H_

#include <cmsis_os.h>


typedef struct
{
	osThreadId_t runner; // task handle
	osThreadAttr_t attr;
	struct {
		osMessageQueueId_t queue;
		//osMutexId_t lock;
	} mailbox; //

} u_ctx ; // struct containing context info for a  instance.
typedef struct {
    u_ctx* rx_ctx;
    u_ctx* tx_ctx;
} ctx_wrapper; // for passing to static void * fn


namespace AppParser {


typedef enum : uint32_t
{
	MOVE_FWD = 0,
	MOVE_BWD,
	MOVE_RIGHT_FWD, // minimum turning radius tbd
	MOVE_LEFT_FWD,
	MOVE_RIGHT_BWD,
	MOVE_LEFT_BWD,
} MOTION_CMD;


typedef struct
{
	MOTION_CMD cmd;
	uint32_t arg;
	bool is_absol;
	bool turn_opt;
} MOTION_PKT_t;


typedef struct {
    uint8_t buffer[10];
    uint32_t length;
} AppMessage_t ;
typedef uint8_t BUF_CMP_t; // buf type

class Listener
{
public:
	Listener(u_ctx *ctx);
	volatile void invoke();
	~Listener( void );
private:
	u_ctx *ctx;
};

class Processor
{
public:
	Processor(u_ctx *rx_ctx, u_ctx *tx_ctx);

	void start();
	~Processor( void );
	u_ctx *this_ctx;
	u_ctx *o_ctx;
	static void processorTask(void *pv);
private:

	static void startImpl(void * _this); //unused
	template <typename T> // no type bounds enforcement, must be uint8_t, char etc.
	static bool isEq(const T &a, const T &b)
	{
		return a == b;
	}
	static MOTION_PKT_t *getMotionCmdFromBytes(BUF_CMP_t *bytes);

};

/* PUBLIC CONSTANTS FOR UART CMDS AND APPLICATION-LAYER CMDS RESPECTIVELY */


//index 0
static constexpr BUF_CMP_t START_CHAR = 'x';

// index 1
static constexpr BUF_CMP_t CMD_CHAR = 'c';
static constexpr BUF_CMP_t REQ_CHAR = 'q';

// index 2
static constexpr BUF_CMP_t MOTOR_CHAR = 'm';
static constexpr BUF_CMP_t SENSOR_CHAR = 's';
static constexpr BUF_CMP_t AUX_CHAR = 'a';

// index 3
static constexpr BUF_CMP_t FWD_CHAR = 'f';
static constexpr BUF_CMP_t BWD_CHAR = 'b';
static constexpr BUF_CMP_t RIGHT_CHAR = 'r';
static constexpr BUF_CMP_t LEFT_CHAR = 'l';

// index 4,5,6
/* This will be a 3-digit number
 * if [2] is MOTOR_CHAR AND [3] is f/b, then this is motion in cm.
 *                      AND [3] is r/l, then this is rotation (relative) in degrees.
 * if [2] .... to be def
*/

// index 7,8
/* [7] f/b char IFF this is a turning cmd (to determine whether the turning radius extends forward or behind) */

// index 9
static constexpr BUF_CMP_t END_CHAR = 'z';



}




#endif /* INC_APP_PARSER_H_ */
