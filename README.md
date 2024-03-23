# MDP
 
## Theory of Operation (STM32 and related SW Abstractions)
### Speed Control
The speed is regulated by independent PID controllers for each motor, and another to minimize the error (i.e. the count difference) between the two encoders. For all distances less than some constant $d_0$, a linear speed mapping is used to prevent overshoot.

### Rotation
The IMU's magnetometer cannot be used due to magnetic interference from the motors. It is hence difficult to derive accurate (absolute) z-axis angular position since that involves integrating over time. The sections below describe, in order, the derivation of usable data, the general implementation of rotation movements, and the application-level angular compensation.

#### Reducing measurement errors
A trivial solution for decreasing the integration error is to sample less often, since we are more interested in the lower frequency component of the gyro. Each sample is denoted as $\omega_{n - kT}$, where $T$ is the inter-sample time and $k \in \mathbb{Z}$.<br>
To provide a sufficiently "smooth" output (i.e. to have step size smaller than T), the samples are interpolated $a$ times per sample. Each interpolated sample $\omega_{n - k \frac{T}{a} \cdot i}$, $i \in 1..a-1$, such that each $\omega_{n - k \frac{T}{a} \cdot i} = \frac{1}{a} \Delta \omega_{n-(k-1)T} \cdot i + \omega_{n-kT}$. $a$ is chosen such that $max( \Delta \phi ) \cdot aT^{-1} \leq \epsilon_{TH}$ as described below.
<br>
In practice, this method is able to yield error accumulation less than 0.0125 deg/s with DLPF avergaging over 8 samples.

#### Turning
To perform a turn, the values $\epsilon = abs(\phi_{cur} - \phi_{target})$ and the optimum turn direction $sgn(\phi_{cur} - \phi_{target})$ (which minimizes $\epsilon$ ) are calculated. In practice, the control loop terminates the rotation whenever $\epsilon$ is within the acceptance threshold $\epsilon_{TH}$.

 Note: The yaw angle $\phi_z$ is derived by $\arctan\left(2 \cdot \left(q_0q_3 + q_1q_2\right), 1 - 2 \cdot \left(q_2^2 + q_3^2\right)\right)$ where $q$ is the quaternion.

#### Angular compensation
It is possible to correct the robot's angle on the fly with the application code in [ISSUE 7](/../../issues/7). It simply performs the operation described in "Turning", or solves the optimization problem that minimizes $\epsilon$ for each 90 degree interval offset of the reference value (which also only works if $\epsilon < 45$)
