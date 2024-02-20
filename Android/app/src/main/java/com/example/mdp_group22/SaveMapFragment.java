package com.example.mdp_group22;

import android.app.DialogFragment;
import android.content.Context;
import android.content.DialogInterface;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.Spinner;
import android.widget.Toast;

import androidx.annotation.Nullable;

import com.example.mdp_group22.MainActivity;
import com.example.mdp_group22.R;

public class SaveMapFragment extends DialogFragment {

    private static final String TAG = "SaveMapFragment";
    private SharedPreferences.Editor editor;

    SharedPreferences sharedPreferences;

    Button saveBtn, cancelBtn;
    String map;
    View rootView;

    @Nullable
    @Override
    public View onCreateView(LayoutInflater inflater, @Nullable ViewGroup container, Bundle savedInstanceState) {
        showLog("Entering onCreateView");
        rootView = inflater.inflate(R.layout.activity_save_map, container, false);
        super.onCreate(savedInstanceState);

        getDialog().setTitle("Save Map");
        sharedPreferences = getActivity().getSharedPreferences("Shared Preferences", Context.MODE_PRIVATE);
        editor = sharedPreferences.edit();

        saveBtn = rootView.findViewById(R.id.saveBtn);
        cancelBtn = rootView.findViewById(R.id.cancelSaveMapBtn);

        map = sharedPreferences.getString("mapChoice","");

        if (savedInstanceState != null)
            map = savedInstanceState.getString("mapChoice");

        final Spinner spinner = (Spinner) rootView.findViewById(R.id.mapDropdownSpinner);
        // Create an ArrayAdapter using the string array and a default spinner layout
        ArrayAdapter<CharSequence> adapter = ArrayAdapter.createFromResource(getActivity(),
                R.array.save_map_array, android.R.layout.simple_spinner_item);
        // Specify the layout to use when the list of choices appears
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        // Apply the adapter to the spinner
        spinner.setAdapter(adapter);

        saveBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                showLog("Clicked saveBtn");
                map = spinner.getSelectedItem().toString();
                editor.putString("mapChoice", map);
                String getObsPos = ((MainActivity)getActivity()).getGridMap().getAllObstacles();
                editor.putString(map, getObsPos);

                Toast.makeText(getActivity(), "Saving " + map, Toast.LENGTH_SHORT).show();
                showLog("Exiting saveBtn");
                editor.commit();
                getDialog().dismiss();
            }
        });

        cancelBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                showLog("Clicked cancelDirectionBtn");
                showLog( "Exiting cancelDirectionBtn");
                getDialog().dismiss();
            }
        });
        showLog("Exiting onCreateView");
        return rootView;
    }

    @Override
    public void onSaveInstanceState(Bundle outState) {
        showLog("Entering onSaveInstanceState");
        super.onSaveInstanceState(outState);
        saveBtn = rootView.findViewById(R.id.saveBtn);
        showLog("Exiting onSaveInstanceState");
        outState.putString(TAG, map);
    }

    @Override
    public void onDismiss(DialogInterface dialog) {
        showLog("Entering onDismiss");
        super.onDismiss(dialog);
        showLog("Exiting onDismiss");
    }

    private void showLog(String message) {
        Log.d(TAG, message);
    }
}
