#include <app_parser.h>
#include "cmsis_os2.h"
#include "stm32f4xx_hal.h"
#include "main.h"
#include "app_main.h"
#include "queue.h"
#include <cstdlib>
#include <cstdio>
#include <cstring>

namespace AppParser {

static volatile BUF_CMP_t uartRxBuf[10];

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
    ctx_wrapper * wrapper_instance = new ctx_wrapper();
    wrapper_instance->rx_ctx = this_ctx;
    wrapper_instance->tx_ctx = o_ctx;

    this->this_ctx->runner = osThreadNew((osThreadFunc_t)&Processor::processorTask,
    		wrapper_instance,
                                    &(this_ctx->attr));
}

void Processor::processorTask(void *pv) {
	HAL_UART_Receive_DMA(&huart3, (BUF_CMP_t*) uartRxBuf, 10);

	ctx_wrapper *wrapper = static_cast<ctx_wrapper*>(pv);

	    // Access rx_ctx and tx_ctx pointers from the wrapper
	    u_ctx *rx_ctx = wrapper->rx_ctx;
	    u_ctx *tx_ctx = wrapper->tx_ctx;

	for (;;) {

		//HAL_GPIO_TogglePin(GPIOE, GPIO_PIN_10);
		osDelay(50);
				osThreadYield();

		/* Let N be the expected input size in bytes.
		 * If N[0] neq start byte, then FLUSH USART DMA buffer.
		 * This is to prevent the buffer from filling with k offset,
		 * where (k + Ni) mod N = k for all integers i and k < N.
		 *
		 * Maybe this algorithm can be improved, as up to 2 messages will be lost.
		 *
		 */
		if (uxQueueMessagesWaiting((QueueHandle_t) rx_ctx->mailbox.queue)) {
			AppMessage_t msg;
			osMessageQueueGet(rx_ctx->mailbox.queue, &msg.buffer, 0, 5);
			// osMessageQueueReset(procCtx.mailbox.queue);

			/* DATA VALIDATION */
			if (!isEq<BUF_CMP_t>(START_CHAR, msg.buffer[0])) {
				HAL_UART_Transmit(&huart3, (BUF_CMP_t*) "WRONG START",
						sizeof("WRONG START"), 10);
			}
			if (!isEq<BUF_CMP_t>(END_CHAR, msg.buffer[9])) {
				HAL_UART_Transmit(&huart3, (BUF_CMP_t*) "WRONG END",
						sizeof("WRONG END"), 10);
			}
			/******************/

			if (isEq<BUF_CMP_t>(REQ_CHAR, msg.buffer[1])) {
				// do request stuff
			} else if (isEq<BUF_CMP_t>(CMD_CHAR, msg.buffer[1])) {
				// do command stuff
				switch (msg.buffer[2]) {
				case MOTOR_CHAR: {
					MOTION_PKT_t *pkt = getMotionCmdFromBytes(
							(uint8_t*) &msg.buffer);

					osMessageQueuePut(tx_ctx->mailbox.queue, pkt, 0, 0);
					break;
				}
				default: {
					// something went wrong..
					break;
				}
				}
			}
			char buf[11] = { 0 };

			snprintf((char*) &buf, 11, "%s", msg.buffer);

			HAL_UART_Transmit(&huart3, (BUF_CMP_t*) buf, sizeof(buf), 100);

			HAL_UART_Receive_DMA(&huart3, (BUF_CMP_t*) uartRxBuf, 10);
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
		HAL_UART_Transmit(&huart3, (BUF_CMP_t*) "FWD CMD", sizeof("FWD CMD"),
				100);
		break;
	}
	case BWD_CHAR: {
		pkt->cmd = MOVE_BWD;
		HAL_UART_Transmit(&huart3, (BUF_CMP_t*) "BWD CMD", sizeof("BWD CMD"),
				100);
		break;
	}
	case LEFT_CHAR: {
		pkt->cmd =
				(bool) (isEq<BUF_CMP_t>(BWD_CHAR, bytes[7])) ?
						MOVE_LEFT_BWD : MOVE_LEFT_FWD;
		HAL_UART_Transmit(&huart3, (BUF_CMP_t*) "L CMD", sizeof("L CMD"), 100);
		break;
	}
	case RIGHT_CHAR: {
		pkt->cmd =
				(bool) (isEq<BUF_CMP_t>(BWD_CHAR, bytes[7])) ?
						MOVE_RIGHT_BWD : MOVE_RIGHT_FWD;
		HAL_UART_Transmit(&huart3, (BUF_CMP_t*) "R CMD", sizeof("R CMD"), 100);
		break;

	}
	default:
		// something went wrong..
		return NULL;
	}

	return pkt;

}
}
