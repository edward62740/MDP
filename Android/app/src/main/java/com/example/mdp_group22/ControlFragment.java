package com.example.mdp_group22;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageButton;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.ToggleButton;
import androidx.annotation.NonNull;
import androidx.fragment.app.Fragment;
import com.example.mdp_group22.MainActivity;
import com.example.mdp_group22.R;
import java.util.Locale;

public class ControlFragment extends Fragment {
    private static final String TAG = "ControlFragment";
    private final MainActivity mainActivity;
    private long imgRecTime, fastestCarTime;
    private SharedPreferences sharedPreferences;
    private ToggleButton imgRecBtn, fastestCarBtn;
    private TextView imgRecText, fastestCarText, robotStatusText;
    private GridMap gridMap;
    private int[] curCoord;
    private String direction;


    public ControlFragment(MainActivity main) {
        this.mainActivity = main;
    }
    public static Handler timerHandler = new Handler();
    public Runnable imgRecTimer = new Runnable() {
        @Override
        public void run() {
            long msTime = System.currentTimeMillis() - imgRecTime;
            int sTime = (int) (msTime / 1000);
            int minuteTime = sTime / 60;
            sTime = sTime % 60;

            if (! mainActivity.imgRecTimerFlag) {
                imgRecText.setText(String.format(Locale.US, "%02d:%02d", minuteTime, sTime));
                timerHandler.postDelayed(this, 500);
            }
        }
    };

    public Runnable fastestCarTimer = new Runnable() {
        @Override
        public void run() {
            long msTime = System.currentTimeMillis() - fastestCarTime;
            int sTime = (int) (msTime / 1000);
            int minuteTime = sTime / 60;
            sTime = sTime % 60;

            if (!mainActivity.fastestCarTimerFlag) {
                fastestCarText.setText(String.format(Locale.US,"%02d:%02d", minuteTime,
                        sTime));
                timerHandler.postDelayed(this, 500);
            }
        }
    };

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
    }

    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        // inflate
        View root = inflater.inflate(R.layout.activity_control, container, false);

        // get shared preferences
        this.sharedPreferences = requireActivity()
                .getSharedPreferences("Shared Preferences", Context.MODE_PRIVATE);

        // initialize all buttons and text views
        ImageButton forwardBtn = this.mainActivity.getUpBtn();
        ImageButton rightBtn = this.mainActivity.getRightBtn();
        ImageButton backBtn = this.mainActivity.getDownBtn();
        ImageButton leftBtn = this.mainActivity.getLeftBtn();
        ImageButton imgRecResetBtn = root.findViewById(R.id.exploreResetImageBtn2);
        ImageButton fastestCarResetBtn = root.findViewById(R.id.fastestResetImageBtn2);
        this.imgRecText = root.findViewById(R.id.exploreTimeTextView2);
        this.fastestCarText = root.findViewById(R.id.fastestTimeTextView2);
        this.imgRecBtn = root.findViewById(R.id.exploreToggleBtn2);
        this.fastestCarBtn = root.findViewById(R.id.fastestToggleBtn2);
        this.robotStatusText = this.mainActivity.getRobotStatusText();

        // default time is 0
        this.fastestCarTime = 0;
        this.imgRecTime = 0;

        // need to get the gridMap to call the private methods
        this.gridMap = this.mainActivity.getGridMap();

        // button listeners. Runs when the buttons are pressed
        forwardBtn.setOnClickListener(view -> {
            // only reacts when robot is placed on gridmap
            if (this.gridMap.getCanDrawRobot()) {
                this.curCoord = this.gridMap.getCurCoord();
                this.direction = this.gridMap.getRobotDirection();
                // handles translation based on existing direction
                switch (this.direction) {
                    case "up":
                        this.gridMap.moveRobot(new int[]{this.curCoord[0], this.curCoord[1] + 1}, 0);
                        break;
                    case "left":
                        this.gridMap.moveRobot(new int[]{this.curCoord[0] - 1, this.curCoord[1]}, 0);
                        break;
                    case "down":
                        this.gridMap.moveRobot(new int[]{this.curCoord[0], this.curCoord[1] - 1}, 0);
                        break;
                    case "right":
                        this.gridMap.moveRobot(new int[]{this.curCoord[0] + 1, this.curCoord[1]}, 0);
                        break;
                }
                // refreshes the UI displayed coordinate of robot
                this.mainActivity.sendMessage("f");
                this.mainActivity.refreshCoordinate();
            }
            else
                this.showToast("Please place robot on map to begin");
        });

        rightBtn.setOnClickListener(view -> {
            if (this.gridMap.getCanDrawRobot()) {
                this.curCoord = this.gridMap.getCurCoord();
                this.direction = this.gridMap.getRobotDirection();
                switch (this.direction) {
                    case "up":
                        this.gridMap.moveRobot(new int[]{this.curCoord[0] + 4, this.curCoord[1] + 2}, -90);
                        break;
                    case "left":
                        this.gridMap.moveRobot(new int[]{this.curCoord[0] - 2, this.curCoord[1] + 4}, -90);
                        break;
                    case "down":
                        this.gridMap.moveRobot(new int[]{this.curCoord[0] - 4, this.curCoord[1] - 2}, -90);
                        break;
                    case "right":
                        this.gridMap.moveRobot(new int[]{this.curCoord[0] + 2, this.curCoord[1] - 4}, -90);
                        break;
                }
                this.mainActivity.sendMessage("tr");
                this.mainActivity.refreshCoordinate();
            }
            else
                this.showToast("Please place robot on map to begin");
        });

        backBtn.setOnClickListener(view -> {
            if (this.gridMap.getCanDrawRobot()) {
                this.curCoord = this.gridMap.getCurCoord();
                this.direction = this.gridMap.getRobotDirection();
                switch (this.direction) {
                    case "up":
                        this.gridMap.moveRobot(new int[]{this.curCoord[0], this.curCoord[1] - 1}, 0);
                        break;
                    case "left":
                        this.gridMap.moveRobot(new int[]{this.curCoord[0] + 1, this.curCoord[1]}, 0);
                        break;
                    case "down":
                        this.gridMap.moveRobot(new int[]{this.curCoord[0], this.curCoord[1] + 1}, 0);
                        break;
                    case "right":
                        this.gridMap.moveRobot(new int[]{this.curCoord[0] - 1, this.curCoord[1]}, 0);
                        break;
                }
                this.mainActivity.sendMessage("r");
                this.mainActivity.refreshCoordinate();
            }
            else {
                this.showToast("Please place robot on map to begin");
            }
        });

        leftBtn.setOnClickListener(view -> {
            if (this.gridMap.getCanDrawRobot()) {
                this.curCoord = this.gridMap.getCurCoord();
                this.direction = this.gridMap.getRobotDirection();
                switch (this.direction) {
                    case "up":
                        this.gridMap.moveRobot(new int[]{this.curCoord[0] - 4, this.curCoord[1] + 1}, 90);
                        break;
                    case "left":
                        this.gridMap.moveRobot(new int[]{this.curCoord[0] - 1, this.curCoord[1] - 4}, 90);
                        break;
                    case "down":
                        this.gridMap.moveRobot(new int[]{this.curCoord[0] + 4, this.curCoord[1] - 1}, 90);
                        break;
                    case "right":
                        this.gridMap.moveRobot(new int[]{this.curCoord[0] + 1, this.curCoord[1] + 4}, 90);
                        break;
                }
                this.mainActivity.sendMessage("tl");
                this.mainActivity.refreshCoordinate();
            }
            else
                this.showToast("Please place robot on map to begin");
        });

        this.imgRecBtn.setOnClickListener(v -> {
            // changed from STOP to START (i.e. done with challenge)
            if (this.imgRecBtn.getText().equals("START")) {
                this.showToast("Image Recognition Completed!!");
                this.robotStatusText.setText(R.string.img_rec_stop);
                timerHandler.removeCallbacks(this.imgRecTimer);
            }
            // changed from START to STOP (i.e. started challenge)
            else if (this.imgRecBtn.getText().equals("STOP")) {
                this.mainActivity.imgRecTimerFlag = false;
                this.showToast("Image Recognition Started!!");
                String getObsPos = this.gridMap.getAllObstacles();
                getObsPos = "OBS|" + getObsPos;
                this.mainActivity.sendMessage(getObsPos);
                this.robotStatusText.setText(R.string.img_rec_start);
                this.imgRecTime = System.currentTimeMillis();
                timerHandler.postDelayed(imgRecTimer, 0);
            }
        });

        this.fastestCarBtn.setOnClickListener(v -> {
            if (this.fastestCarBtn.getText().equals("START")) {
                this.showToast("Fastest Car Stopped!");
                this.robotStatusText.setText(R.string.fastest_car_stop);
                timerHandler.removeCallbacks(fastestCarTimer);
            }
            // changed from START to STOP (i.e., challenge started)
            else if (fastestCarBtn.getText().equals("STOP")) {
                this.showToast("Fastest Car started!");
                this.mainActivity.sendMessage("STM|Start");
                this.mainActivity.fastestCarTimerFlag = false;
                this.robotStatusText.setText(R.string.fastest_car_start);
                this.fastestCarTime = System.currentTimeMillis();
                timerHandler.postDelayed(fastestCarTimer, 0);
            }
        });

        imgRecResetBtn.setOnClickListener(v -> {
            this.showToast("Resetting image recognition challenge timer...");
            this.imgRecText.setText(R.string.timer_default_val);
            this.robotStatusText.setText(R.string.robot_status_na);
            if (this.imgRecBtn.isChecked())
                this.imgRecBtn.toggle();
            timerHandler.removeCallbacks(imgRecTimer);
        });

        fastestCarResetBtn.setOnClickListener(view -> {
            this.showToast("Resetting fastest car challenge timer...");
            this.fastestCarText.setText(R.string.timer_default_val);
            this.robotStatusText.setText(R.string.robot_status_na);
            if (this.fastestCarBtn.isChecked()){
                this.fastestCarBtn.toggle();
            }
            timerHandler.removeCallbacks(fastestCarTimer);
        });

        return root;
    }

    private void debugMessage(String message) {
        Log.d(TAG, message);
    }
    private void showToast(String message) {
        Toast.makeText(getContext(), message, Toast.LENGTH_SHORT).show();
    }

    @Override
    public void onDestroy(){
        super.onDestroy();
    }
}