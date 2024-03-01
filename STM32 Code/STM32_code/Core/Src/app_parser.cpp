#include <app_parser.h>
#include "cmsis_os2.h"
#include "stm32f4xx_hal.h"
#include "main.h"
#include "app_main.h"
#include "app_motion.h"
#include "queue.h"
#include <cstdlib>
#include <cstdio>
#include <cstring>

namespace AppParser {

bool Processor::_signal_obstr = false;
bool Processor::_obstr_txed = false;

static volatile BUF_CMP_t uartRxBuf[10];
static volatile BUF_CMP_t uartOKBuf[10];
Listener::Listener(u_ctx *ctx) {
	this->ctx = ctx;
}

Listener::~Listener() {
}
;
// not needed

/*! called from ISR */
volatile void Listener::invoke() {
	//osMutexRelease(this->ctx->mailbox.lock);
	AppMessage_t msg;
	memcpy(&msg.buffer, (const BUF_CMP_t*) &uartRxBuf, 10);
	memset((BUF_CMP_t*) &uartRxBuf, 0, 10);
	osStatus_t tmp = osMessageQueuePut(ctx->mailbox.queue, &msg, 0, 0);
	//HAL_UART_Transmit(&huart3, (uint8_t *)ibuf, sizeof(ibuf), 10);
	HAL_GPIO_TogglePin(GPIOE, GPIO_PIN_10);

	//HAL_UART_Receive_DMA(&huart3, (uint8_t *) aRxBuffer, 5);
}

Processor::Processor(u_ctx *rx_ctx, u_ctx *tx_ctx) {
	this->this_ctx = rx_ctx;
	this->o_ctx = tx_ctx;
	this->this_ctx->mailbox.queue = osMessageQueueNew(10, sizeof(AppMessage_t),
	NULL);
}

Processor::~Processor() {
}
;
// not needed

void Processor::startImpl(void *_this) // hardfaults on queue for some reason so made static
		{
	//static_cast<Processor *>(_this)->processorTask();
}

void Processor::start(void) {
	ctx_wrapper *wrapper_instance = new ctx_wrapper();
	wrapper_instance->rx_ctx = this_ctx;
	wrapper_instance->tx_ctx = o_ctx;
// pass context information to the thread fn since there is some issue with making the fn a class instance.
// note that this_ctx refers to this class and o_ctx refers to the (o)ther class, i.e. the destination, MotionController
	this->this_ctx->runner = osThreadNew(
			(osThreadFunc_t) Processor::processorTask, wrapper_instance,
			&(this_ctx->attr));

	return;
}

void Processor::processorTask(void *pv) {
	HAL_UART_Receive_DMA(&huart3, (BUF_CMP_t*) uartRxBuf, 10);

	ctx_wrapper *wrapper = static_cast<ctx_wrapper*>(pv);

	// Access rx_ctx and tx_ctx pointers from the wrapper
	u_ctx *rx_ctx = wrapper->rx_ctx;
	u_ctx *tx_ctx = wrapper->tx_ctx;

	for (;;) {

		//HAL_GPIO_TogglePin(GPIOE, GPIO_PIN_10);
		is_task_alive_struct.proc = true;

		osDelay(50);
		osThreadYield();

		/* Let N be the expected input size in bytes.
		 * There are two valid conditions at this point:
		 * - Input buffer is zero because no data was received
		 * - Input buffer is also zero because N bytes were received and copied to the queue
		 *
		 * This section resets the DMA buffer if there are k non-zero bytes in the DMA buffer,
		 * for any k < N.
		 * This is to prevent the buffer from filling with k offset,
		 * where (k + Ni) mod N = k for all integers i and k < N.
		 *
		 * Note that this algorithm has the obvious downside of wiping the buffer should it run
		 * while the N bytes are being received. The chance of this is pretty low, so its good
		 * enough for this purpose..
		 *
		 * Any alternative to get per-byte interrupt etc., will require rewriting of the HAL funcs
		 * or polling mechanism.
		 */
		uint32_t buf_fill = 0;
		for (uint32_t i = 0; i < sizeof(uartRxBuf); i++) {
			if (uartRxBuf[i] != 0) {
				HAL_UART_DMAStop(&huart3);
				HAL_UART_Receive_DMA(&huart3, (BUF_CMP_t*) uartRxBuf, 10);
				memset((BUF_CMP_t*) &uartRxBuf, 0, 10);
				break;
			}
		}

		/* end buffer cleaning algorithm */

		sensor_data.ql = osMessageQueueGetCount(rx_ctx->mailbox.queue);
		if (uxQueueMessagesWaiting((QueueHandle_t) rx_ctx->mailbox.queue)) {

			AppMessage_t msg;
			osMessageQueueGet(rx_ctx->mailbox.queue, &msg.buffer, 0, 5);
			// osMessageQueueReset(procCtx.mailbox.queue);

			/* DATA VALIDATION */
			if (!isEq<BUF_CMP_t>(START_CHAR, msg.buffer[0])) {
				HAL_UART_Transmit(&huart3, (BUF_CMP_t*) nack, sizeof(nack), 10);
			}
			if (!isEq<BUF_CMP_t>(END_CHAR, msg.buffer[9])) {
				HAL_UART_Transmit(&huart3, (BUF_CMP_t*) nack, sizeof(nack), 10);
			}
			/******************/

			// do request stuff
			if (isEq<BUF_CMP_t>(REQ_CHAR, msg.buffer[1])) {
				if (isEq(SENSOR_CHAR, msg.buffer[2])) {
					returnSensorRequestCmd(msg.buffer[3]);
				} else if (isEq(AUX_CHAR, msg.buffer[2])) {
					if (isEq(LAST_HALT_CHAR, msg.buffer[3])) {
						uint8_t tx_buf[25] = { 0 };
						snprintf((char*) &tx_buf, sizeof(tx_buf), "%ld",
										sensor_data.last_halt_val);
								HAL_UART_Transmit(&huart3, (BUF_CMP_t*) tx_buf, strlen((char*) tx_buf),
										10);
					}
				}

			} else if (isEq<BUF_CMP_t>(CMD_CHAR, msg.buffer[1])) {
				// do command stuff
				if (isEq(HALT_CHAR, msg.buffer[3])) {
					_ext_sig_halt();
				}
				switch (msg.buffer[2]) {
				case MOTOR_CHAR: {
					MOTION_PKT_t *pkt = getMotionCmdFromBytes(
							(uint8_t*) &msg.buffer);
					if (pkt == NULL) {
						HAL_UART_Transmit(&huart3, (BUF_CMP_t*) nack,
								sizeof(nack), 10);
						break;
					}

					osMessageQueuePut(tx_ctx->mailbox.queue, pkt, 0, 0);
					HAL_UART_Transmit(&huart3, (BUF_CMP_t*) ack, sizeof(ack),
							10);
					break;
				}
				case SENSOR_CHAR: {
					uint32_t val = strtol((const char*) &msg.buffer[4], NULL,
							10);
					if (val == 0)
						break;

					switch (msg.buffer[3]) {

					case IR_L_CHAR: {
						sensor_data.ir_dist_th_L = (float) val;
						if (val == 999)
							sensor_data.ir_dist_th_L = 0;
						HAL_UART_Transmit(&huart3, (BUF_CMP_t*) ack,
								sizeof(ack), 10);
						break;
					}
					case IR_R_CHAR: {
						sensor_data.ir_dist_th_R = (float) val;
						if (val == 999)
							sensor_data.ir_dist_th_R = 0;
						HAL_UART_Transmit(&huart3, (BUF_CMP_t*) ack,
								sizeof(ack), 10);
						break;
					}
					default: {
						// something went wrong..

					}

					}

				}
				default: {
					// something went wrong..
				}
				}
			} else {
				HAL_UART_Transmit(&huart3, (BUF_CMP_t*) nack, sizeof(nack), 10);
			}

			HAL_UART_Receive_DMA(&huart3, (BUF_CMP_t*) uartRxBuf, 10); // re-enable DMA buf for rx
		} else if (_signal_obstr) // specifically lower priority than RX
		{
			if (!_obstr_txed)
				HAL_UART_Transmit(&huart3, (BUF_CMP_t*) obstr, sizeof(obstr),
						10);
			_obstr_txed = true;
		}

	}

}

void Processor::returnSensorRequestCmd(BUF_CMP_t id) {
	uint8_t tx_buf[25] = { 0 };

	switch (id) {
	case IR_L_CHAR: {
		snprintf((char*) &tx_buf, sizeof(tx_buf), "%4.2f",
				sensor_data.ir_distL);
		HAL_UART_Transmit(&huart3, (BUF_CMP_t*) tx_buf, strlen((char*) tx_buf),
				10);
		break;
	}
	case IR_R_CHAR: {
		snprintf((char*) &tx_buf, sizeof(tx_buf), "%4.2f",
				sensor_data.ir_distR);
		HAL_UART_Transmit(&huart3, (BUF_CMP_t*) tx_buf, strlen((char*) tx_buf),
				10);
		break;
	}
	case USOUND_CHAR: {
		snprintf((char*) &tx_buf, sizeof(tx_buf), "%4.2f",
				sensor_data.usonic_dist);
		HAL_UART_Transmit(&huart3, (BUF_CMP_t*) tx_buf, strlen((char*) tx_buf),
				10);
		break;
	}
	case GY_Z_CHAR: {
		snprintf((char*) &tx_buf, sizeof(tx_buf), "%4.2f",
				sensor_data.imu->gyro[2]);
		HAL_UART_Transmit(&huart3, (BUF_CMP_t*) tx_buf, strlen((char*) tx_buf),
				10);
		break;
	}
	case QTRN_YAW_CHAR: {
		snprintf((char*) &tx_buf, sizeof(tx_buf), "%4.2f", sensor_data.yaw_abs);
		HAL_UART_Transmit(&huart3, (BUF_CMP_t*) tx_buf, strlen((char*) tx_buf),
				10);
		break;
	}
	case QTRN_ALL_CHAR: {
		snprintf((char*) &tx_buf, sizeof(tx_buf), "%4.1f;%4.1f;%4.1f;%4.1f",
				sensor_data.imu->q[0], sensor_data.imu->q[1],
				sensor_data.imu->q[2], sensor_data.imu->q[3]);
		HAL_UART_Transmit(&huart3, (BUF_CMP_t*) tx_buf, strlen((char*) tx_buf),
				10);
		break;
	}
	default: {
		HAL_UART_Transmit(&huart3, (BUF_CMP_t*) nack, sizeof(nack), 10);
	}
	}
}

MOTION_PKT_t* Processor::getMotionCmdFromBytes(BUF_CMP_t *bytes) {

	uint32_t val = strtol((const char*) &bytes[4], NULL, 10);
	if (val == 0)
		return NULL; // invalid input or no action
	MOTION_PKT_t *pkt = new MOTION_PKT_t();
	pkt->arg = val;
	switch (bytes[3]) {
	case FWD_CHAR: {
		pkt->cmd = MOVE_FWD;
		break;
	}
	case BWD_CHAR: {
		pkt->cmd = MOVE_BWD;
		break;
	}
	case LEFT_CHAR: {
		pkt->cmd =
				(bool) (isEq<BUF_CMP_t>(BWD_CHAR, bytes[7])) ?
						MOVE_LEFT_BWD : MOVE_LEFT_FWD;
		break;
	}
	case RIGHT_CHAR: {
		pkt->cmd =
				(bool) (isEq<BUF_CMP_t>(BWD_CHAR, bytes[7])) ?
						MOVE_RIGHT_BWD : MOVE_RIGHT_FWD;
		break;

	}

	default:
		// something went wrong..
		return NULL;
	}

	return pkt;

}

}
