package com.example.mdp_group22;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.ProgressDialog;
import android.bluetooth.BluetoothDevice;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.util.Log;
import android.widget.ImageButton;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.ToggleButton;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.fragment.app.FragmentPagerAdapter;
import androidx.localbroadcastmanager.content.LocalBroadcastManager;
import androidx.viewpager.widget.ViewPager;

import com.example.mdp_group22.BluetoothChatFragment;
import com.example.mdp_group22.BluetoothConnectionService;
import com.example.mdp_group22.BluetoothPopUp;
import com.example.mdp_group22.ControlFragment;
import com.example.mdp_group22.GridMap;
import com.example.mdp_group22.MapTabFragment;
import com.example.mdp_group22.SectionsPagerAdapter;

import com.google.android.material.tabs.TabLayout;

import java.nio.charset.Charset;


public class MainActivity extends AppCompatActivity {
    // Declaration Variables
    private static final String TAG = "MainActivity";
    private SharedPreferences sharedPreferences;
    private SharedPreferences.Editor editor;
    private Context context;
    private GridMap gridMap;
    private TextView robotXCoordText, robotYCoordText, robotDirectionText;
    private TextView robotStatusText;
    private static TextView bluetoothStatus, bluetoothDevice;
    private ImageButton upBtn, downBtn, leftBtn, rightBtn;
    private ProgressDialog btDisconnectDialog;
    public boolean imgRecTimerFlag = false;
    public boolean fastestCarTimerFlag = false;
    private BluetoothChatFragment btFragment;
    private MapTabFragment mapTabFragment;
    private ControlFragment controlFragment;


    /**
     * onCreate is called when the app runs
     *
     * @param savedInstanceState If the activity is being re-initialized after
     *                           previously being shut down then this Bundle contains the data it most
     *                           recently supplied in {@link #onSaveInstanceState}.  <b><i>Note: Otherwise it is null.</i></b>
     */
    @Override
    protected void onCreate(Bundle savedInstanceState) {

        // remember to always call the super method
        super.onCreate(savedInstanceState);

        // choose which layout to be displayed, in this case the activity_main layout
        this.setContentView(R.layout.activity_main);

        // SectionsPagerAdapter extends from FragmentPagerAdapter
        SectionsPagerAdapter sectionsPagerAdapter = new SectionsPagerAdapter(getSupportFragmentManager(),
                FragmentPagerAdapter.BEHAVIOR_RESUME_ONLY_CURRENT_FRAGMENT);

        // adds different fragments that comes into view when clicked
        // CHAT is for sending and receiving BT message to and from STM
        // MAP CONFIG is for configuring the map layout
        // CHALLENGE provides quick access to execute the algo for img recognition & fastest path
        this.btFragment = new BluetoothChatFragment(this);
        this.mapTabFragment = new MapTabFragment(this);
        this.controlFragment = new ControlFragment(this);
        this.gridMap = new GridMap(this);
        sectionsPagerAdapter.addFragment(this.btFragment, "CHAT");
        sectionsPagerAdapter.addFragment(this.mapTabFragment, "MAP CONFIG");
        sectionsPagerAdapter.addFragment(this.controlFragment, "CHALLENGE");

        // TODO
        // dont know what this section does, best to not touch
        ViewPager viewPager = findViewById(R.id.view_pager);
        viewPager.setAdapter(sectionsPagerAdapter);
        viewPager.setOffscreenPageLimit(2);

        TabLayout tabs = findViewById(R.id.tabs);
        tabs.setupWithViewPager(viewPager);

        LocalBroadcastManager
                .getInstance(this)
                .registerReceiver(messageReceiver, new IntentFilter("incomingMessage"));

        // Set up sharedPreferences
        this.context = getApplicationContext();
        this.sharedPreferences();
        this.editor.putString("message", "");
        this.editor.putString("direction", "None");
        this.editor.putString("connStatus", "Disconnected");
        this.editor.commit();

        // Toolbar
        ImageButton bluetoothButton = findViewById(R.id.bluetoothButton);
        bluetoothButton.setOnClickListener(v -> {
            Intent popup = new Intent(MainActivity.this, BluetoothPopUp.class);
            this.startActivity(popup);
        });

        // Bluetooth Status
        MainActivity.bluetoothStatus = findViewById(R.id.bluetoothStatus);
        MainActivity.bluetoothDevice = findViewById(R.id.bluetoothConnectedDevice);

        // Map
        this.gridMap = findViewById(R.id.mapView);
        this.robotXCoordText = findViewById(R.id.xAxisTextView);
        this.robotYCoordText = findViewById(R.id.yAxisTextView);
        this.robotDirectionText = findViewById(R.id.directionAxisTextView);

        // Controller to manually control robot movement
        this.upBtn = findViewById(R.id.upBtn);
        this.downBtn = findViewById(R.id.downBtn);
        this.leftBtn = findViewById(R.id.leftBtn);
        this.rightBtn = findViewById(R.id.rightBtn);

        // Robot Status
        this.robotStatusText = findViewById(R.id.robotStatus);

        // pops up when BT is disconnected
        this.btDisconnectDialog = new ProgressDialog(MainActivity.this);
        this.btDisconnectDialog.setMessage("Waiting for other device to reconnect...");
        this.btDisconnectDialog.setCancelable(false);
        this.btDisconnectDialog.setButton(
                DialogInterface.BUTTON_NEGATIVE,
                "Cancel",
                (dialog, which) -> dialog.dismiss()
        );
    }

    public GridMap getGridMap() {
        return this.gridMap;
    }

    public TextView getRobotStatusText() {
        return this.robotStatusText;
    }

    public ImageButton getUpBtn() {
        return this.upBtn;
    }

    public ImageButton getDownBtn() {
        return this.downBtn;
    }

    public ImageButton getLeftBtn() {
        return this.leftBtn;
    }

    public ImageButton getRightBtn() {
        return this.rightBtn;
    }

    public static TextView getBluetoothStatus() {
        return bluetoothStatus;
    }

    public static TextView getConnectedDevice() {
        return bluetoothDevice;
    }

    public void sharedPreferences() {
        this.sharedPreferences = this.getSharedPreferences(this.context);
        this.editor = this.sharedPreferences.edit();
    }

    public void sendMessage(String message) {
        this.editor = this.sharedPreferences.edit();
//        message += "\n";
        if (BluetoothConnectionService.BluetoothConnectionStatus) {
            byte[] bytes = message.getBytes(Charset.defaultCharset());
            // Send the size of bytes to be sent, followed by a newline character
            //String sizeMessage = String.valueOf(bytes.length) + "\n";
            //byte[] sizeBytes = sizeMessage.getBytes(Charset.defaultCharset());
            //BluetoothConnectionService.write(sizeBytes);
            BluetoothConnectionService.write(bytes);
        }
        this.printMessage(message);
    }

    public void printMessage(String message) {
        this.btFragment.getMessageReceivedTextView().append(message);
    }

    public void refreshDirection(String direction) {
        this.gridMap.setRobotDirection(direction);
        this.robotDirectionText.setText(this.sharedPreferences.getString("direction", ""));
    }

    public void refreshCoordinate() {
        this.robotXCoordText.setText(String.valueOf(this.gridMap.getCurCoord()[0]));
        this.robotYCoordText.setText(String.valueOf(this.gridMap.getCurCoord()[1]));
        this.robotDirectionText.setText(this.sharedPreferences.getString("direction", ""));
    }

    private void showLog(String message) {
        Log.d(TAG, message);
    }

    private SharedPreferences getSharedPreferences(Context context) {
        return context.getSharedPreferences("Shared Preferences", Context.MODE_PRIVATE);
    }
    private final BroadcastReceiver mBroadcastReceiver5 = new BroadcastReceiver() {
        @SuppressLint("MissingPermission")
        @Override
        public void onReceive(Context context, Intent intent) {
            BluetoothDevice mDevice = intent.getParcelableExtra("Device");
            String status = intent.getStringExtra("Status");
            sharedPreferences();

            if (status.equals("connected")) {
                try {
                    btDisconnectDialog.dismiss();
                } catch (NullPointerException e) {
                    e.printStackTrace();
                }
                Toast.makeText(MainActivity.this, "Device now connected to "
                        + mDevice.getName(), Toast.LENGTH_SHORT).show();
                editor.putString("connStatus", "Connected to " + mDevice.getName());
            } else if (status.equals("disconnected")) {
                Toast.makeText(MainActivity.this, "Disconnected from "
                        + mDevice.getName(), Toast.LENGTH_SHORT).show();
                editor.putString("connStatus", "Disconnected");
                btDisconnectDialog.show();
            }
            editor.commit();
        }
    };

    BroadcastReceiver messageReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String message = intent.getStringExtra("receivedMessage");
            System.out.println("debug" + message);
            if (message.contains("IMG")) {
                String[] cmd = message.split("-");
                gridMap.updateImageID(cmd[1], cmd[2]);
            } else if (message.contains("UPDATE")) {
                String[] cmd = message.split("-");
                int xPos = (int) Float.parseFloat(cmd[1]);
                int yPos = (int) Float.parseFloat(cmd[2]);
                double bearing;
                if (cmd[3].contains("N")) {
                    bearing = (double) -1 * Float.parseFloat(cmd[3].substring(1));
                } else {
                    bearing = Float.parseFloat(cmd[3]);
                }
                gridMap.moveRobot(new int[]{xPos, yPos}, bearing);
            } else if (message.equals("ENDED")) {
                ToggleButton imgRecBtn = findViewById(R.id.exploreToggleBtn2);
                ToggleButton fastestCarBtn = findViewById(R.id.fastestToggleBtn2);

                if (imgRecBtn.isChecked()) {
                    imgRecTimerFlag = true;
                    imgRecBtn.setChecked(false);
                    robotStatusText.setText(R.string.image_rec_end);
                    ControlFragment.timerHandler.removeCallbacks(controlFragment.imgRecTimer);
                } else if (fastestCarBtn.isChecked()) {
                    imgRecTimerFlag = true;
                    fastestCarBtn.setChecked(false);
                    robotStatusText.setText(R.string.fastest_car_end);
                    ControlFragment.timerHandler.removeCallbacks(controlFragment.fastestCarTimer);
                }
            }
        }
    };


    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == 1) {
            if (resultCode == Activity.RESULT_OK) {
                BluetoothDevice mBTDevice = data.getExtras().getParcelable("mBTDevice");
            }
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        try {
            LocalBroadcastManager.getInstance(this).unregisterReceiver(messageReceiver);
            LocalBroadcastManager.getInstance(this).unregisterReceiver(mBroadcastReceiver5);
        } catch (IllegalArgumentException e) {
            e.printStackTrace();
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        try {
            LocalBroadcastManager.getInstance(this).unregisterReceiver(mBroadcastReceiver5);
        } catch (IllegalArgumentException e) {
            e.printStackTrace();
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        try {
            IntentFilter filter2 = new IntentFilter("ConnectionStatus");
            LocalBroadcastManager.getInstance(this).registerReceiver(mBroadcastReceiver5, filter2);
        } catch (IllegalArgumentException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void onSaveInstanceState(@NonNull Bundle outState) {
        this.showLog("Entering onSaveInstanceState");
        super.onSaveInstanceState(outState);

        outState.putString(TAG, "onSaveInstanceState");
        this.showLog("Exiting onSaveInstanceState");
    }
}