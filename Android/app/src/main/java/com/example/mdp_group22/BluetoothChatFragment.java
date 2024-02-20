package com.example.mdp_group22;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.text.method.ScrollingMovementMethod;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.fragment.app.Fragment;
import androidx.localbroadcastmanager.content.LocalBroadcastManager;

import com.example.mdp_group22.MainActivity;
import com.example.mdp_group22.R;

import java.nio.charset.Charset;

public class BluetoothChatFragment extends Fragment {

    private static final String TAG = "CommsFragment";

    private SharedPreferences sharedPreferences;

    private TextView receivedMsgText;

    private EditText editText;

    private final MainActivity mainActivity;

    public BluetoothChatFragment(MainActivity main) {
        this.mainActivity = main;
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LocalBroadcastManager.getInstance(this.requireContext())
                .registerReceiver(this.mReceiver, new IntentFilter("incomingMessage"));
    }

    @Override
    public View onCreateView(
            @NonNull LayoutInflater inflater, ViewGroup container,
            Bundle savedInstanceState) {

        View root = inflater.inflate(R.layout.activity_comms, container, false);

        ImageButton send = root.findViewById(R.id.btnSend);

        this.receivedMsgText = root.findViewById(R.id.receivedMsgText);
        this.receivedMsgText.setMovementMethod(new ScrollingMovementMethod());
        this.editText = root.findViewById(R.id.editText);
        this.sharedPreferences = this.requireActivity()
                .getSharedPreferences("Shared Preferences", Context.MODE_PRIVATE);

        send.setOnClickListener(view -> {
            String sentText = "" + this.editText.getText().toString();
            SharedPreferences.Editor editor = sharedPreferences.edit();
            editor.putString("message", sharedPreferences
                    .getString("message", "") + '\n' + sentText);
            editor.apply();
            this.receivedMsgText.append(sentText + "\n");
            this.editText.setText("");

            if (BluetoothConnectionService.BluetoothConnectionStatus) {
                byte[] bytes = sentText.getBytes(Charset.defaultCharset());
                BluetoothConnectionService.write(bytes);
            }
        });
        return root;
    }

    public TextView getMessageReceivedTextView() {
        return this.receivedMsgText;
    }

    private final BroadcastReceiver mReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String text = intent.getStringExtra("receivedMessage");
            if (text != null) {
                receivedMsgText.append(text + "\n");
            } else {
                Log.d(TAG, "Received intent without 'receivedMessage' extra or it is null");
            }
        }

    };

    private void debugMessage(String debugContext) {
        Log.d(BluetoothChatFragment.TAG, debugContext);
    }
}