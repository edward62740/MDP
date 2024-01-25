#include <app_parser.h>
#include <app_motion.h>
#include "app_main.h"
#include "cmsis_os.h"
#include "main.h"
#include "stm32f4xx_hal.h"
#include "stm32f4xx_hal_uart.h"
#include "ICM20948.h"
#include <cmath>
#include <cstdio>

sensorData_t sensor_data; // public variables shared across all files.
bool test_run = false;
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
	test_run = true;
}
/* Instances and shared variables for AppParser and AppMotion namespace class instances */
osMutexAttr_t procLock_attr;
//osMutexId_t procLockHandle = osMutexNew(&procLock_attr);
osThreadId_t procTaskHandle;
const osThreadAttr_t procTask_attr = { .name = "procTask", .stack_size = 1024,
		.priority = (osPriority_t) osPriorityBelowNormal7, };

static u_ctx procCtx = { .runner = procTaskHandle, .attr = procTask_attr,
		.mailbox = { .queue = NULL } };


osThreadId_t ctrlTaskHandle;
const osThreadAttr_t ctrlTask_attr = { .name = "ctrlTask", .stack_size = 1024,
		.priority = (osPriority_t) osPriorityBelowNormal7, };

osMessageQueueId_t ctrlQueue = osMessageQueueNew(10, sizeof(AppParser::MOTION_PKT_t), NULL);
/*nonstatic*/ u_ctx ctrlCtx = { .runner = ctrlTaskHandle, .attr = ctrlTask_attr,
		.mailbox = { .queue = ctrlQueue } };

AppMotion::MotionController controller(&ctrlCtx);
AppParser::Processor processor(&procCtx, &ctrlCtx);
AppParser::Listener listener(&procCtx);
/*****************************************************************************************/


void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
	//__HAL_UART_CLEAR_OREFLAG(&huart3);
	if (huart == &huart3) {
		listener.invoke();
	}
}

/*
 * This function initializes the C++ stuff, called from within main() context.
 */
void initializeCPPconstructs(void) {
	//procTaskHandle = osThreadNew(processorTask, NULL, &procTask_attr);

	processor.start();
	//osThreadNew((osThreadFunc_t)&controller.motionTask,
	    		//&ctrlCtx,
	                                   // &(ctrlCtx.attr));
				controller.start();
	//htim1.Instance->CCR1 = 153;
}


//BEGIN TEST SECTION
#include "stm32f4xx_hal.h" /* Needed for I2C */
#define __Gyro_Read_Z(_I2C, readGyroData, gyroZ) ({ \
	HAL_I2C_Mem_Read(_I2C,0x0C << 1, 0x37, I2C_MEMADD_SIZE_8BIT, readGyroData, 2, 10); \
	gyroZ = readGyroData[0] << 8 | readGyroData[1]; \
})
uint8_t readGyroZData[2];
//END TEST SECTION
void robotTurn(float *targetAngle) {

	float angleNow = 0;
	float gyroZ = 0;
	char sbuf[10] = { 0 };

	uint32_t last_curTask_tick = HAL_GetTick();
	do {
		if (HAL_GetTick() - last_curTask_tick >= 10) { // sample gyro every 10ms
			//__Gyro_Read_Z(&hi2c1, readGyroZData, gyroZ);
			angleNow += imu.gyro[2] * 0.01;
			if (abs(angleNow - *targetAngle) < 10)
				break;
			last_curTask_tick = HAL_GetTick();
			uint16_t len = sprintf(&sbuf[0], "%5.2f\r\n", angleNow);

			HAL_UART_Transmit(&huart3, (uint8_t*) sbuf, len, 10);
		}
	} while (1);
	*targetAngle = 0;


}
void sensorTask(void *pv) {

	IMU_Initialise(&imu, &hi2c1);

	osDelay(50);
	Gyro_calibrate(&imu);
	Mag_init(&imu);

	sensor_data.imu = &imu;
	uint8_t readGyroZData[2];

	/**I2C scanner for debug purposes **/
	printf("Scanning I2C bus:\r\n");
	HAL_StatusTypeDef result;
	uint8_t i;
	for (i = 1; i < 128; i++) {
		/*
		 * the HAL wants a left aligned i2c address
		 * &hi2c1 is the handle
		 * (uint16_t)(i<<1) is the i2c address left aligned
		 * retries 2
		 * timeout 2
		 */
		result = HAL_I2C_IsDeviceReady(&hi2c1, (uint16_t) (i << 1), 2, 2);
		if (result != HAL_OK) // HAL_ERROR or HAL_BUSY or HAL_TIMEOUT
				{
			printf("."); // No ACK received at that address
		}
		if (result == HAL_OK) {
			printf("0x%X", i); // Received an ACK at that address
		}
	}
	printf("\r\n");

	//magCalICM20948(&imu, &imu.mag_bias, &imu.mag_scale);
	char sbuf[100] = { 0 };
	printf("%d\n", imu.mag_bias[0]);
	printf("%d\n", imu.mag_bias[1]);
	printf("%d\n", imu.mag_bias[2]);
	uint32_t timeNow = HAL_GetTick();
	float dir = 0;

	float DEG2RAD = 0.017453292519943295769236907684886f;

	float mRes = 10.0f * 4912.0f / 32760.0f;
	for (;;) {

		//setLeftPWM(1000); // was 1000, 2000
		//setRightPWM(2000);
		//robotTurnPID(&targetAngle, 0);
		float angle = 100;
		//robotTurn(&angle);
		//uint8_t sbuf[60] = { 0 };
		/* USER CODE END WHILE */

		IMU_AccelRead(&imu);
		IMU_GyroRead(&imu);
		//Mag_read(&imu);


		/*MahonyQuaternionUpdate(&imu, imu.acc[0], imu.acc[1], imu.acc[2],
		 (float) imu.gyro[0] * DEG2RAD, (float) imu.gyro[1] * DEG2RAD,
		 (float) imu.gyro[2] * DEG2RAD,
		 (float) imu.mag[1] * mRes - imu.mag_bias[1],
		 (float) imu.mag[0] * mRes - imu.mag_bias[0],
		 (float) imu.mag[2] * mRes - imu.mag_bias[2], 0.1);
		 double pitch = atan2(imu.acc[1],
		 (sqrt((imu.acc[0] * imu.acc[0]) + (imu.acc[2] * imu.acc[2]))));
		 double roll = atan2(-imu.acc[0],
		 (sqrt((imu.acc[1] * imu.acc[1]) + (imu.acc[2] * imu.acc[2]))));
		 float Yh = (imu.mag[1] * cos(roll)) - (imu.mag[2] * sin(roll));
		 float Xh = (imu.mag[0] * cos(pitch))
		 + (imu.mag[1] * sin(roll) * sin(pitch))
		 + (imu.mag[2] * cos(roll) * sin(pitch));
		 */
		//float yaw = atan2(Yh, Xh);
		//timeNow = HAL_GetTick();
		/*float yaw = atan2(2.0f * (imu.q[1] * imu.q[2] + imu.q[0] * imu.q[3]),
		 imu.q[0] * imu.q[0] + imu.q[1] * imu.q[1] - imu.q[2] * imu.q[2]
		 - imu.q[3] * imu.q[3]) * 57.295779513082320876798154814105f;*/
		uint16_t len = sprintf(&sbuf[0],
				"%5.2f,%5.2f,%5.2f,%5.2f,%5.2f,%5.2f,%5.2f,%5.2f,%5.2f\r\n",
				imu.acc[0], imu.acc[1], imu.acc[2], imu.gyro[0], imu.gyro[1],
				imu.gyro[2], dir, 0, 0);

	//	HAL_UART_Transmit(&huart3, (uint8_t*) sbuf, len, 10);
		//	HAL_UART_Receive_IT(&huart3, (uint8_t*) aRxBuffer, 5);
		osDelay(65);

	}
}
