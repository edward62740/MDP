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

import androidx.annotation.Nullable;

import com.example.mdp_group22.MainActivity;
import com.example.mdp_group22.R;

public class LoadMapFragment extends DialogFragment {

    private static final String TAG = "LoadMapFragment";
    private SharedPreferences.Editor editor;
    private SharedPreferences sharedPreferences;
    private String mapData;
    private GridMap gridMap;

    @Nullable
    @Override
    public View onCreateView(LayoutInflater inflater, @Nullable ViewGroup container, Bundle savedInstanceState) {
        showLog("Entering onCreateView");
        View rootView = inflater.inflate(R.layout.activity_load_map, container, false);
        super.onCreate(savedInstanceState);

        this.getDialog().setTitle("Load Map");
        this.sharedPreferences = getActivity().getSharedPreferences("Shared Preferences", Context.MODE_PRIVATE);
        this.editor = this.sharedPreferences.edit();

        Button loadMapBtn = rootView.findViewById(R.id.loadMapBtn);
        Button cancelLoadMapBtn = rootView.findViewById(R.id.cancelLoadMapBtn);

        this.mapData = this.sharedPreferences.getString("mapChoice","");
        this.gridMap = ((MainActivity) getActivity()).getGridMap();

        if (savedInstanceState != null)
            this.mapData = savedInstanceState.getString("mapChoice");

        final Spinner spinner = (Spinner) rootView.findViewById(R.id.mapDropdownSpinner);
        // Create an ArrayAdapter using the string array and a default spinner layout
        ArrayAdapter<CharSequence> adapter = ArrayAdapter.createFromResource(getActivity(),
                R.array.save_map_array, android.R.layout.simple_spinner_item);
        // Specify the layout to use when the list of choices appears
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        // Apply the adapter to the spinner
        spinner.setAdapter(adapter);

        loadMapBtn.setOnClickListener(view -> {
            this.showLog("Clicked loadMapBtn");
            this.mapData = spinner.getSelectedItem().toString();
            this.editor.putString("mapChoice", mapData);
            String obsPos = this.sharedPreferences.getString(this.mapData,"");
            if(! obsPos.equals("")) {
                String[] obstaclePosition = obsPos.split("\\|");
                for (String s : obstaclePosition) {
                    String[] coords = s.split(",");
                    coords[3] = "OB" + coords[3];
                    this.gridMap.addObstacleCoord(Integer.parseInt(coords[0]), Integer.parseInt(coords[1]), coords[3]);
                    String direction;
                    switch (coords[2]) {
                        case "E":
                            direction = "East";
                            break;
                        case "S":
                            direction = "South";
                            break;
                        case "W":
                            direction = "West";
                            break;
                        default:
                            direction = "North";
                    }
                    this.gridMap.setImageBearing(direction, Integer.parseInt(coords[0]), Integer.parseInt(coords[1]));
                }
                this.gridMap.invalidate();
                showLog("Exiting Load Button");
            }
            this.getDialog().dismiss();
        });

        cancelLoadMapBtn.setOnClickListener(view -> {
            this.getDialog().dismiss();
        });
        showLog("Exiting onCreateView");
        return rootView;
    }

    @Override
    public void onSaveInstanceState(Bundle outState) {
        this.showLog("Entering onSaveInstanceState");
        super.onSaveInstanceState(outState);
        this.showLog("Exiting onSaveInstanceState");
        outState.putString(TAG, this.mapData);
    }

    @Override
    public void onDismiss(DialogInterface dialog) {
        this.showLog("Entering onDismiss");
        super.onDismiss(dialog);
        this.showLog("Exiting onDismiss");
    }

    private void showLog(String message) {
        Log.d(TAG, message);
    }
}

