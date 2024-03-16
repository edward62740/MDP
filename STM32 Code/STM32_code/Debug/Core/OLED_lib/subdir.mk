################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (10.3-2021.10)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Core/OLED_lib/oled.c 

C_DEPS += \
./Core/OLED_lib/oled.d 

OBJS += \
./Core/OLED_lib/oled.o 


# Each subdirectory must supply rules for building sources it contributes
Core/OLED_lib/%.o Core/OLED_lib/%.su: ../Core/OLED_lib/%.c Core/OLED_lib/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_HAL_DRIVER -DSTM32F407xx -DSTM32_THREAD_SAFE_STRATEGY=4 -c -I"C:/Users/Edward/Documents/GitHub/MDP/STM32 Code/STM32_code/Core/ICM20948_lib" -I"C:/Users/Edward/Documents/GitHub/MDP/STM32 Code/STM32_code/Core/OLED_lib" -I"C:/Users/Edward/Documents/GitHub/MDP/STM32 Code/STM32_code/Core/Inc" -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -I../Core/ThreadSafe -I../Core/Inc -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Core-2f-OLED_lib

clean-Core-2f-OLED_lib:
	-$(RM) ./Core/OLED_lib/oled.d ./Core/OLED_lib/oled.o ./Core/OLED_lib/oled.su

.PHONY: clean-Core-2f-OLED_lib

