package com.example.mdp_group22;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.Context;
import android.content.DialogInterface;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Point;
import android.util.AttributeSet;
import android.util.Log;
import android.view.DragEvent;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowManager;
import android.widget.ArrayAdapter;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.ToggleButton;

import androidx.annotation.Nullable;

import com.example.mdp_group22.R;

import java.util.ArrayList;
import java.util.Arrays;


public class GridMap extends View {
    private class Cell {
        protected final float startX, startY, endX, endY;
        protected Paint paint;
        private String type;
        private int id = -1;

        private Cell(float startX, float startY, float endX, float endY, Paint paint, String type) {
            this.startX = startX;
            this.startY = startY;
            this.endX = endX;
            this.endY = endY;
            this.paint = paint;
            this.type = type;
        }

        public void setType(String type) {
            this.type = type;
            switch (type) {
                case "obstacle":
                    this.paint = obstacleColor;
                    break;
                case "end":
                    this.paint = endColor;
                    break;
                case "start":
                    this.paint = startColor;
                    break;
                case "waypoint":
                    this.paint = waypointColor;
                    break;
                case "unexplored":
                    this.paint = unexploredColor;
                    break;
                case "explored":
                    this.paint = exploredColor;
                    break;
                case "arrow":
                    this.paint = arrowColor;
                    break;
                case "fastestPath":
                    this.paint = fastestPathColor;
                    break;
                case "image":
                    this.paint = obstacleColor;
                default:
                    Logd("setType default: " + type);
                    break;
            }
        }

        public String getType() {
            return this.type;
        }

        public void setId(int id) {
            this.id = id;
        }

        public int getId() {
            return this.id;
        }
    }
    private static final String TAG = "GridMap";
    private SharedPreferences sharedPreferences;
    private final Paint blackPaint = new Paint();
    private final Paint whitePaint = new Paint();
    private final Paint greenPaint = new Paint();
    private final Paint obstacleColor = new Paint();
    private final Paint robotColor = new Paint();
    private final Paint endColor = new Paint();
    private final Paint startColor = new Paint();
    private final Paint waypointColor = new Paint();
    private final Paint unexploredColor = new Paint();
    private final Paint exploredColor = new Paint();
    private final Paint arrowColor = new Paint();
    private final Paint fastestPathColor = new Paint();
    private String robotDirection = "None";
    public static double robotBearing = 90;
    private int[] startCoord;
    private int[] curCoord;
    private ArrayList<int[]> obstacleCoord = new ArrayList<>();
    private boolean canDrawRobot = false;
    private boolean startCoordStatus = false;
    private boolean setObstacleStatus = false;
    private static final int COL = 20;
    private static final int ROW = 20;
    private static float cellSize;
    private static Cell[][] cells;
    private boolean mapDrawn = false;
    public String[][] OBSTACLE_LIST = new String[20][20];
    public String[][] IMAGE_LIST = new String[20][20];
    public static String[][] IMAGE_BEARING = new String[20][20];
    static ClipData clipData;
    static Object localState;
    int initialColumn, initialRow;

    public GridMap(Context c) {
        super(c);
        initMap();
    }

    public GridMap(Context context, @Nullable AttributeSet attrs) {
        super(context, attrs);
        initMap();
        this.blackPaint.setStyle(Paint.Style.FILL_AND_STROKE);
        this.whitePaint.setColor(Color.WHITE);
        this.whitePaint.setTextSize(15);
        this.whitePaint.setTextAlign(Paint.Align.CENTER);
        this.greenPaint.setColor(getResources().getColor(R.color.grassColor));
        this.greenPaint.setStrokeWidth(8);
        this.obstacleColor.setColor(getResources().getColor(R.color.rockColor));
        this.robotColor.setColor(getResources().getColor(R.color.light_blue));
        this.robotColor.setStrokeWidth(2);
        this.endColor.setColor(Color.RED);
        this.startColor.setColor(Color.CYAN);
        this.waypointColor.setColor(Color.GREEN);
        this.unexploredColor.setColor(getResources().getColor(R.color.lightBlue));
        this.exploredColor.setColor(getResources().getColor(R.color.exploredColor2));
        this.arrowColor.setColor(Color.BLACK);
        this.fastestPathColor.setColor(Color.MAGENTA);
        this.startCoord = new int[]{-1, -1};
        this.curCoord = new int[]{-1, -1};

        Paint newpaint = new Paint();
        newpaint.setColor(Color.TRANSPARENT);
        // get shared preferences
        sharedPreferences = getContext().getSharedPreferences("Shared Preferences",
                Context.MODE_PRIVATE);
    }

    private void initMap() {
        /* initialize 3 2d arrays
            1. OBSTACLE_LIST: 2d array of cells. If a cell has obstacle, the id is found here
            2. IMAGE_LIST: 2d array of cells. If a cell has obstacle and identified, the image id is found here
            3. IMAGE_BEARING: 2d array of cells. If a cell has obstacle, the facing direction is found here.
        */
        for (int outter = 0; outter < this.OBSTACLE_LIST.length; outter++) {
            String[] row = new String[this.OBSTACLE_LIST[outter].length];
            Arrays.fill(row, "");
            this.OBSTACLE_LIST[outter] = row;
        }

        for (int outter = 0; outter < this.IMAGE_LIST.length; outter++) {
            String[] row = new String[this.IMAGE_LIST[outter].length];
            Arrays.fill(row, "");
            this.IMAGE_LIST[outter] = row;
        }

        for (int outter = 0; outter < GridMap.IMAGE_BEARING.length; outter++) {
            String[] row = new String[GridMap.IMAGE_BEARING[outter].length];
            Arrays.fill(row, "");
            GridMap.IMAGE_BEARING[outter] = row;
        }
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (!mapDrawn) {
            this.createCell();
            mapDrawn = true;
        }

        this.drawIndividualCell(canvas);
        this.drawGridLines(canvas);
        this.drawGridNumber(canvas);
        if (this.getCanDrawRobot())
            this.drawRobot(canvas, curCoord);
        this.drawObstacles(canvas);
    }

    private void createCell() {
        cells = new Cell[COL + 1][ROW + 1];     // COL is horizontal; ROW is vertical
        cellSize = (float) getWidth() / (COL + 1);

        for (int x = 0; x <= COL; x++)
            for (int y = 0; y <= ROW; y++)
                cells[x][y] = new Cell(
                        x * cellSize + (cellSize / 30),
                        y * cellSize + (cellSize / 30),
                        (x + 1) * cellSize,
                        (y + 1) * cellSize,
                        unexploredColor,
                        "unexplored"
                );
    }

    private void drawIndividualCell(Canvas canvas) {
        // y starts from 1 since 1st column is used for index labels
        for (int x = 1; x <= COL; x++)
            for (int y = 0; y < ROW; y++)
                canvas.drawRect(
                        cells[x][y].startX,
                        cells[x][y].startY,
                        cells[x][y].endX,
                        cells[x][y].endY,
                        cells[x][y].paint
                );
    }

    private void drawGridLines(Canvas canvas) {
        for (int x = 0; x < ROW; x ++)
            canvas.drawLine(
                    cells[x][0].startX - (cellSize / 30) + cellSize,
                    cells[x][0].startY + (cellSize / 30),
                    cells[x][20].startX - (cellSize / 30) + cellSize,
                    cells[x][20].startY + (cellSize / 30),
                    whitePaint
            );

        for (int y = 0; y < COL; y ++)
            canvas.drawLine(
                    cells[0][y].startX - (cellSize / 30) + cellSize,
                    cells[0][y].startY + (cellSize / 30),
                    cells[20][y].startX - (cellSize / 30) + cellSize,
                    cells[20][y].startY + (cellSize / 30),
                    whitePaint
            );
    }

    private void drawGridNumber(Canvas canvas) {
        Paint textPaint = new Paint();
        textPaint.setTextSize(17);
        textPaint.setColor(Color.BLACK);

        for (int x = 1; x <= COL; x++) {
            if (x >= 10)
                canvas.drawText(
                        Integer.toString(x),
                        cells[x][20].startX + (cellSize / 5),
                        cells[x][20].startY + (cellSize / 1.5f),
                        textPaint
                );
            else
                canvas.drawText(
                        Integer.toString(x),
                        cells[x][20].startX + (cellSize / 2.5f),
                        cells[x][20].startY + (cellSize / 1.5f),
                        textPaint
                );
        }

        for (int y = 0; y < ROW; y++) {
            if ((20 - y) >= 10)
                canvas.drawText(
                        Integer.toString(ROW - y),
                        cells[0][y].startX + (cellSize / 5),
                        cells[0][y].startY + (cellSize / 1.5f),
                        textPaint
                );
            else
                canvas.drawText(
                        Integer.toString(ROW - y),
                        cells[0][y].startX + (cellSize / 2.5f),
                        cells[0][y].startY + (cellSize / 1.5f),
                        textPaint
                );
        }
    }

    public boolean getCanDrawRobot() {
        return this.canDrawRobot;
    }

    public void setCanDrawRobot(boolean canDrawRobot) {
        this.canDrawRobot = canDrawRobot;
    }

    private void drawRobot(Canvas canvas, int[] curCoord) {
        float xCoord, yCoord;
        BitmapFactory.Options op = new BitmapFactory.Options();
        Bitmap bm, mapscalable;
        int robotX = curCoord[0];
        int robotY = curCoord[1];

        if (! (robotX == -1 && robotY == -1)) {
            op.inMutable = true;
            switch (this.getRobotDirection()) {
                case "up":
                    if (robotY < 2 || robotY > 20 || robotX < 1 || robotX > 19) {
                        Toast.makeText(
                                this.getContext(),
                                "Error with drawing robot (out of bound)",
                                Toast.LENGTH_SHORT
                        ).show();
                        this.setCanDrawRobot(false);
                    } else {
                        xCoord = cells[robotX][20 - robotY].startX;
                        yCoord = cells[robotX][20 - robotY].startY;
                        bm = BitmapFactory.decodeResource(getResources(),R.drawable.car_face_up, op);
                        mapscalable = Bitmap.createScaledBitmap(bm, 51,51, true);
                        canvas.drawBitmap(mapscalable, xCoord, yCoord, null);
                    }
                    break;

                case "down":
                    if (robotY < 1 ||robotY > 19 || robotX < 2 || robotX > 20) {
                        Toast.makeText(
                                this.getContext(),
                                "Error with drawing robot (out of bound)",
                                Toast.LENGTH_SHORT
                        ).show();
                        this.setCanDrawRobot(false);
                    } else {
                        xCoord = cells[robotX - 1][20 - (robotY + 1)].startX;
                        yCoord = cells[robotX - 1][20 - (robotY + 1)].startY;
                        bm = BitmapFactory.decodeResource(getResources(),R.drawable.car_face_down, op);
                        mapscalable = Bitmap.createScaledBitmap(bm, 51,51, true);
                        canvas.drawBitmap(mapscalable, xCoord, yCoord, null);

                    }
                    break;
                case "right":
                    if (robotY < 2 || robotY > 20 || robotX < 2 || robotX > 20) {
                        Toast.makeText(
                                this.getContext(),
                                "Error with drawing robot (out of bound)",
                                Toast.LENGTH_SHORT
                        ).show();
                        this.setCanDrawRobot(false);
                    } else {
                        xCoord = cells[robotX - 1][20 - robotY].startX;
                        yCoord = cells[robotX - 1][20 - robotY].startY;
                        bm = BitmapFactory.decodeResource(getResources(),R.drawable.car_face_right, op);
                        mapscalable = Bitmap.createScaledBitmap(bm, 51,51, true);
                        canvas.drawBitmap(mapscalable, xCoord, yCoord, null);
                    }
                    break;

                case "left":
                    if (robotY < 1 || robotY > 19 ||robotX < 1 || robotX > 19) {
                        Toast.makeText(
                                this.getContext(),
                                "Error with drawing robot (out of bound)",
                                Toast.LENGTH_SHORT
                        ).show();
                        this.setCanDrawRobot(false);
                    } else {
                        xCoord = cells[robotX][20 - (robotY - 1)].startX;
                        yCoord = cells[robotX][20 - (robotY + 1)].startY;
                        bm = BitmapFactory.decodeResource(getResources(),R.drawable.car_face_left, op);
                        mapscalable = Bitmap.createScaledBitmap(bm, 51,51, true);
                        canvas.drawBitmap(mapscalable, xCoord, yCoord, null);
                    }
                    break;

                default:
                    Toast.makeText(
                            this.getContext(),
                            "Error with drawing robot (unknown direction)",
                            Toast.LENGTH_SHORT
                    ).show();
                    break;
            }
        }
    }

    private void drawObstacles(Canvas canvas) {
        Paint textPaint = new Paint();
        textPaint.setColor(Color.WHITE);
        textPaint.setTextAlign(Paint.Align.CENTER);

        for (int i = 0; i < 20; i++) {
            for (int j = 0; j < 20; j++) {
                String displayedText;
                if (! IMAGE_LIST[19 - i][j].equals("")) {
                    displayedText = IMAGE_LIST[19 - i][j];
                    textPaint.setTextSize(17);
                    canvas.drawText(
                            displayedText,
                            cells[j + 1][19 - i].startX + ((cells[1][1].endX - cells[1][1].startX) / 2),
                            cells[j + 1][i].startY + ((cells[1][1].endY - cells[1][1].startY) / 2) + 10,
                            textPaint
                    );
                }
                else {
                    displayedText = OBSTACLE_LIST[19 - i][j];
                    textPaint.setTextSize(11);
                    canvas.drawText(
                            displayedText,
                            cells[j + 1][19 - i].startX + ((cells[1][1].endX - cells[1][1].startX) / 2),
                            cells[j + 1][i].startY + ((cells[1][1].endY - cells[1][1].startY) / 2) + 10,
                            textPaint
                    );

                    // color the face direction
                    switch (IMAGE_BEARING[19 - i][j]) {
                        case "North":
                            canvas.drawLine(
                                    cells[j + 1][20 - i].startX,
                                    cells[j + 1][i].startY,
                                    cells[j + 1][20 - i].endX,
                                    cells[j + 1][i].startY,
                                    greenPaint
                            );
                            break;
                        case "South":
                            canvas.drawLine(
                                    cells[j + 1][20 - i].startX,
                                    cells[j + 1][i].startY + cellSize,
                                    cells[j + 1][20 - i].endX,
                                    cells[j + 1][i].startY + cellSize,
                                    greenPaint
                            );
                            break;
                        case "East":
                            canvas.drawLine(
                                    cells[j + 1][20 - i].startX + cellSize,
                                    cells[j + 1][i].startY,
                                    cells[j + 1][20 - i].startX + cellSize,
                                    cells[j + 1][i].endY,
                                    greenPaint
                            );
                            break;
                        case "West":
                            canvas.drawLine(
                                    cells[j + 1][20 - i].startX,
                                    cells[j + 1][i].startY,
                                    cells[j + 1][20 - i].startX,
                                    cells[j + 1][i].endY,
                                    greenPaint
                            );
                            break;
                    }
                }
                // draw image id

            }
        }
    }

    public String getRobotDirection() {
        return robotDirection;
    }

    public void setSetObstacleStatus(boolean status) {
        setObstacleStatus = status;
    }

    public boolean getSetObstacleStatus() {
        return setObstacleStatus;
    }

    public void setStartCoordStatus(boolean status) {
        startCoordStatus = status;
    }

    private boolean getStartCoordStatus() {
        return startCoordStatus;
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (event.getAction() == MotionEvent.ACTION_DOWN) {
            this.initialColumn = (int) (event.getX() / cellSize);
            this.initialRow = this.convertRow((int) (event.getY() / cellSize));
            String obstacleID;
            String obstacleBearing;
            ToggleButton setStartPointToggleBtn = ((Activity)this.getContext())
                    .findViewById(R.id.startpointToggleBtn);

            if (MapTabFragment.dragStatus) {
                // if the drag location has no obstacles, do nothing
                if (this.getObstacleID(this.initialColumn, this.initialRow).equals("")) {
                    return false;
                }
                DragShadowBuilder dragShadowBuilder = new MyDragShadowBuilder(this);
                this.startDragAndDrop(null, dragShadowBuilder, null, 0);
            }

            // start change obstacle
            if (MapTabFragment.changeObstacleStatus) {
                obstacleID = this.getObstacleID(this.initialColumn, this.initialRow);
                obstacleBearing = this.getImageBearing(this.initialColumn, this.initialRow);
                // if touch on empty cell, do nothing
                if (obstacleID.equals("")) {
                    return false;
                } else {
                    final int tRow = this.initialRow;
                    final int tCol = this.initialColumn;

                    AlertDialog.Builder mBuilder = new AlertDialog.Builder(this.getContext());
                    View mView = ((Activity) this.getContext()).getLayoutInflater()
                            .inflate(R.layout.activity_dialog_change_obstacle,
                                    null);
                    mBuilder.setTitle("Change Existing Obstacle ID/Bearing");
                    final Spinner mIDSpinner = mView.findViewById(R.id.imageIDSpinner2);
                    final Spinner mBearingSpinner = mView.findViewById(R.id.bearingSpinner2);

                    ArrayAdapter<CharSequence> adapter = ArrayAdapter.createFromResource(
                            this.getContext(), R.array.imageID_array,
                            android.R.layout.simple_spinner_item);
                    adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
                    mIDSpinner.setAdapter(adapter);
                    ArrayAdapter<CharSequence> adapter2 = ArrayAdapter.createFromResource(
                            this.getContext(), R.array.imageBearing_array,
                            android.R.layout.simple_spinner_item);
                    adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
                    mBearingSpinner.setAdapter(adapter2);
                    mIDSpinner.setSelection(Integer.parseInt(obstacleID.substring(2)));

                    switch (obstacleBearing) {
                        case "North": mBearingSpinner.setSelection(0);
                            break;
                        case "South": mBearingSpinner.setSelection(1);
                            break;
                        case "East": mBearingSpinner.setSelection(2);
                            break;
                        case "West": mBearingSpinner.setSelection(3);
                    }

                    final String oldID = obstacleID;
                    mBuilder.setPositiveButton("OK", new DialogInterface.OnClickListener() {
                        @Override
                        public void onClick(DialogInterface dialogInterface, int i) {
                            String newID = mIDSpinner.getSelectedItem().toString();
                            String newBearing = mBearingSpinner.getSelectedItem().toString();

                            removeObstacle(oldID, initialColumn, initialRow);
                            addObstacleCoord(tCol, tRow, newID);
                            setObstacleID(newID, tCol, tRow);
                            setImageBearing(newBearing, tCol, tRow);

                            invalidate();
                        }
                    });

                    // dismiss
                    mBuilder.setNegativeButton("Cancel", new DialogInterface.OnClickListener() {
                        @Override
                        public void onClick(DialogInterface dialogInterface, int i) {
                            dialogInterface.dismiss();
                        }
                    });

                    mBuilder.setView(mView);
                    AlertDialog dialog = mBuilder.create();
                    dialog.show();
                    Window window =  dialog.getWindow();
                    WindowManager.LayoutParams layoutParams = new WindowManager.LayoutParams();
                    layoutParams.width = 150;
                    window.setLayout(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
                }
            }

            if (this.startCoordStatus) {
                String direction = getRobotDirection();
                boolean flag = false;
                if (this.canDrawRobot) {
                    if (direction.equals("None")) {
                        direction = "up";
                    }

                    switch (direction) {
                        case "up":
                            if (this.initialColumn > 0 && this.initialColumn < 20
                                    && this.initialRow > 1 && this.initialRow <= 20) {
                                flag = true;
                            }
                            break;

                        case "left":
                            if (this.initialColumn > 0 && this.initialColumn < 20
                                    && this.initialRow >= 1 && this.initialRow < 20) {
                                flag = true;
                            }
                            break;

                        case "right":
                            if (this.initialColumn > 1 && this.initialColumn <= 20
                                    && this.initialRow > 1 && this.initialRow <= 20) {
                                flag = true;
                            }
                            break;

                        case "down":
                            if (this.initialColumn > 1 && this.initialColumn <= 20
                                    && this.initialRow > 0 && this.initialRow < 20) {
                                flag = true;
                            }
                            break;
                    }

                    for (int i = 1; i < COL; i ++) {
                        for (int j = 1; j < ROW; j ++) {
                            if (cells[i][j].getType().equals("robot")) {
                                this.updateCells("explored", i, j);
                            }
                        }
                    }
                }

                if (flag) {
                    this.setStartCoord(initialColumn, initialRow);
                    this.startCoordStatus = false;
                    this.updateRobotAxis(this.initialColumn, this.initialRow, direction);
                    if (setStartPointToggleBtn.isChecked())
                        setStartPointToggleBtn.toggle();
                }

                this.invalidate();
                return true;
            }

            // add id and the image bearing, popup to ask for user input
            if (this.setObstacleStatus) {
                if (this.initialRow <= 20 && this.initialColumn <= 20) {
                    this.setImageBearing("North", this.initialColumn, this.initialRow);
                    this.addObstacleCoord(initialColumn, initialRow, "OB0");
                }
                this.invalidate();
                return true;
            }
        }
        return false;
    }

    public void setStartCoord(int col, int row) {
        String direction = this.getRobotDirection();
        if (direction.equals("None")) {
            direction = "up";
        }
        switch (direction) {
            case "up":
                if (col > 0 && col < 20 && row > 1 && row <= 20) {
                    this.startCoord[0] = col;
                    this.startCoord[1] = row;
                } else {
                    return;
                }
                break;

            case "left":
                if (col > 0 && col < 20 && row >= 1 && row < 20) {
                    this.startCoord[0] = col;
                    this.startCoord[1] = row;
                } else {
                    return;
                }
                break;

            case "right":
                if (col > 1 && col <= 20 && row > 1 && row <= 20) {
                    this.startCoord[0] = col;
                    this.startCoord[1] = row;
                } else {
                    return;
                }
                break;

            case "down":
                if (col > 1 && col <= 20 && row > 0 && row < 20) {
                    this.startCoord[0] = col;
                    this.startCoord[1] = row;
                } else {
                    return;
                }
                break;
        }

        if (this.getStartCoordStatus())
            this.setCurCoord(col, row, direction);
    }

    public void setCurCoord(int col, int row, String direction) {
        if (col < 1 || col > 20 || row < 1 || row > 20) {
            return;
        }

        this.curCoord[0] = col;
        this.curCoord[1] = row;
        this.setRobotDirection(direction);
        this.updateRobotAxis(col, row, direction);
        this.updateCells("explored", col, row);

        switch (direction) {
            case "up":
                this.updateCells("explored", col + 1, row - 1);
                this.updateCells("explored", col + 1, row);
                this.updateCells("explored", col, row - 1);
                break;

            case "down":
                this.updateCells("explored", col - 1, row + 1);
                this.updateCells("explored", col - 1, row);
                this.updateCells("explored", col, row + 1);
                break;

            case "left":
                this.updateCells("explored", col + 1, row + 1);
                this.updateCells("explored", col + 1, row);
                this.updateCells("explored", col, row + 1);
                break;

            case "right":
                this.updateCells("explored", col - 1, row - 1);
                this.updateCells("explored", col - 1, row);
                this.updateCells("explored", col, row - 1);
                break;
        }
    }

    public int[] getCurCoord() {
        return this.curCoord;
    }

    private int convertRow(int row) {
        return (20 - row);
    }
    public void setRobotDirection(String direction) {
        this.sharedPreferences = this.getContext().getSharedPreferences("Shared Preferences",
                Context.MODE_PRIVATE);
        SharedPreferences.Editor editor = this.sharedPreferences.edit();
        this.robotDirection = direction;
        editor.putString("direction", direction);
        editor.apply();
        this.invalidate();
    }

    private void updateRobotAxis(int col, int row, String direction) {
        TextView xAxisTextView =  ((Activity)this.getContext()).findViewById(R.id.xAxisTextView);
        TextView yAxisTextView =  ((Activity)this.getContext()).findViewById(R.id.yAxisTextView);
        TextView directionAxisTextView =  ((Activity)this.getContext())
                .findViewById(R.id.directionAxisTextView);

        xAxisTextView.setText(String.format(Integer.toString(col)));
        yAxisTextView.setText(String.format(Integer.toString(row)));
        directionAxisTextView.setText(direction);
    }

    public void addObstacleCoord(int col, int row, String obstacleID) {
        int parsedID = Integer.parseInt(obstacleID.substring(2));
        int[] obstacleCoord = new int[]{col, row, parsedID};
        this.obstacleCoord.add(obstacleCoord);
        this.setObstacleID(obstacleID, col, row);
        this.updateCells("obstacle", col, row);
    }

    public ArrayList<int[]> getObstacleCoord() {
        return this.obstacleCoord;
    }
    private static void Logd(String message) {
        Log.d(TAG, message);
    }

    @Override
    public boolean onDragEvent(DragEvent dragEvent) {
        GridMap.clipData = dragEvent.getClipData();
        GridMap.localState = dragEvent.getLocalState();

        int endColumn, endRow;
        String obstacleID = this.getObstacleID(this.initialColumn, this.initialRow);
        String imageBearing = this.getImageBearing(this.initialColumn, this.initialRow);

        // If the currently dragged cell is empty, do nothing
        if (obstacleID.equals("")) {
            return false;
        }

        // Drop outside of map entirely (anywhere on the screen)
        if (! dragEvent.getResult() && dragEvent.getAction() == DragEvent.ACTION_DRAG_ENDED) {
            this.removeObstacle(obstacleID, this.initialColumn, this.initialRow);
        }

        // Drop on the map (including the indices row and col)
        if (dragEvent.getAction() == DragEvent.ACTION_DROP) {
            endColumn = (int) (dragEvent.getX() / GridMap.cellSize);
            endRow = this.convertRow((int) (dragEvent.getY() / GridMap.cellSize));

            // If dropped on indices row and col
            if (endColumn <= 0 || endRow <= 0) {
                this.removeObstacle(obstacleID, this.initialColumn, this.initialRow);
            }

            // If dropped within gridmap, shift it to new position unless already got existing
            else if (1 <= this.initialColumn && this.initialColumn <= 20
                    && 1 <= this.initialRow && this.initialRow <= 20
                    && endColumn <= 20 && endRow <= 20) {
                // Only execute if nothing is present at drag location
                if (this.getObstacleID(endColumn, endRow).equals("")) {
                    this.removeObstacle(obstacleID, this.initialColumn, this.initialRow);
                    this.addObstacleCoord(endColumn, endRow, obstacleID);
                    this.setImageBearing(imageBearing, endColumn, endRow);
                }
            } else {
                throw new IllegalArgumentException("Drag event failed");
            }
        }
        this.invalidate();
        return true;
    }

    public void removeObstacle(String obstacleID, int x, int y) {
        int obstacleX, obstacleY;
        for (int i = 0; i < this.getObstacleCoord().size(); i ++) {
            int[] currentObstacle = this.getObstacleCoord().get(i);
            int[] targetObstacle = new int[]{x, y, Integer.parseInt(obstacleID.substring(2))};
            if (Arrays.equals(currentObstacle, targetObstacle)) {
                obstacleX = currentObstacle[0];
                obstacleY = currentObstacle[1];
                this.setObstacleID("", obstacleX, obstacleY);
                this.setImageBearing("", obstacleX, obstacleY);
                this.updateCells("unexplored", obstacleX, obstacleY);
                this.getObstacleCoord().remove(currentObstacle);
                return;
            }
        }
    }

    public void toggleCheckedBtn(String buttonName) {
        ToggleButton setStartPointToggleBtn = ((Activity)this.getContext())
                .findViewById(R.id.startpointToggleBtn);
        ToggleButton obstacleImageBtn = ((Activity)this.getContext())
                .findViewById(R.id.addObstacleBtn);

        if (!buttonName.equals("setStartPointToggleBtn"))
            if (setStartPointToggleBtn.isChecked()) {
                this.setStartCoordStatus(false);
                setStartPointToggleBtn.toggle();
            }
        if (!buttonName.equals("obstacleImageBtn"))
            if (obstacleImageBtn.isChecked()) {
                this.setSetObstacleStatus(false);
                obstacleImageBtn.toggle();
            }        
    }

    public void resetMap(boolean hardReset) {
        TextView robotStatusTextView =  ((Activity)this.getContext())
                .findViewById(R.id.robotStatus);
        this.updateRobotAxis(0, 0, "None");
        robotStatusTextView.setText(R.string.status_not_available);

        this.toggleCheckedBtn("None");
        this.setStartCoord(-1, -1);
        this.setCurCoord(-1, -1, "None");
        this.setRobotDirection("None");
        this.setCanDrawRobot(false);
        GridMap.robotBearing = 90;
        this.obstacleCoord = new ArrayList<>();
        mapDrawn = !hardReset;

        for (int i = 1; i <= 20; i++) {
            for (int j = 1; j <= 20; j++) {
                this.setObstacleID("", i, j);
                this.setImageID("", i, j);
                this.setImageBearing("", i, j);
            }
        }
        this.invalidate();
    }

    public void moveRobot(int[] nextCoord, double angle) {
        String robotDirection = this.getRobotDirection();   // current direction of the robot
        boolean flag = false;
        GridMap.robotBearing += angle;
        double offset = GridMap.robotBearing % 360;
        offset = this.handleAngle(offset);
        // facing N
        if (offset > 45 && offset <= 135) {
            if (nextCoord[1] <= 20 && nextCoord[1] > 1 && nextCoord[0] >= 1 && nextCoord[0] < 20
                    && validMove(nextCoord, "up")) {
                flag = true;
                robotDirection = "up";
            }
        }
        // facing W
        else if (offset > 135 && offset <= 225) {
            if (nextCoord[1] < 20 && nextCoord[1] >= 1 && nextCoord[0] >= 1 && nextCoord[0] < 20
                    && validMove(nextCoord, "left")) {
                flag = true;
                robotDirection = "left";
            }
        }
        // facing S
        else if (offset > 225 && offset < 315) {
            if (nextCoord[1] < 20 && nextCoord[1] >= 1 && nextCoord[0] > 1 && nextCoord[0] <= 20
                    && validMove(nextCoord, "down")) {
                flag = true;
                robotDirection = "down";
            }
        }
        // facing E
        else {
            if (nextCoord[1] <= 20 && nextCoord[1] > 1 && nextCoord[0] > 1 && nextCoord[0] <= 20
                    && validMove(nextCoord, "right")) {
                flag = true;
                robotDirection = "right";
            }
        }

        if (flag) {
            this.extrapolateRobot(nextCoord, robotDirection);
        } else {
            GridMap.robotBearing -= angle;  //revert angle change
        }
        this.invalidate();
    }

    public double handleAngle(double angle) {
        while (angle < 0) {
            angle += 360;
        }
        return angle;
    }

    public void extrapolateRobot(int[] nextCoord, String robotDirection) {
        int[] curCoord = this.getCurCoord();
        Logd(robotDirection + "is the robot direction");
        // same x-coord
        if (curCoord[0] == nextCoord[0]) {
            switch (robotDirection) {
                case "up":
                    if (nextCoord[1] > curCoord[1]) {
                        for (int i = curCoord[1]; i <= nextCoord[1]; i ++) {
                            this.updateCells("explored", curCoord[0], i);
                            this.updateCells("explored", curCoord[0] + 1, i);
                        }
                    } else {
                        for (int i = nextCoord[1]; i <= curCoord[1]; i ++) {
                            this.updateCells("explored", curCoord[0], i);
                            this.updateCells("explored", curCoord[0] + 1, i);
                        }
                    }
                    break;

                case "down":
                    if (nextCoord[1] > curCoord[1]) {
                        for (int i = curCoord[1]; i <= nextCoord[1]; i ++) {
                            this.updateCells("explored", curCoord[0], i);
                            this.updateCells("explored", curCoord[0] - 1, i);
                        }
                    } else {
                        for (int i = nextCoord[1]; i <= curCoord[1]; i ++) {
                            this.updateCells("explored", curCoord[0], i);
                            this.updateCells("explored", curCoord[0] - 1, i);

                        }
                    }
                    break;
            }
        }
        // same y-coord
        if (curCoord[1] == nextCoord[1]) {
            switch (robotDirection) {
                case "left":
                    if (nextCoord[0] > curCoord[0]) {
                        for (int i = curCoord[0]; i <= nextCoord[0]; i ++) {
                            this.updateCells("explored", i, curCoord[1]);
                            this.updateCells("explored", i, curCoord[1] + 1);
                        }
                    } else {
                        for (int i = nextCoord[0]; i <= curCoord[0]; i ++) {
                            this.updateCells("explored", i, curCoord[1]);
                            this.updateCells("explored", i, curCoord[1] + 1);
                        }
                    }
                    break;

                case "right":
                    if (nextCoord[0] > curCoord[0]) {
                        for (int i = curCoord[0]; i <= nextCoord[0]; i ++) {
                            this.updateCells("explored", i, curCoord[1]);
                            this.updateCells("explored", i, curCoord[1] - 1);
                        }
                    } else {
                        for (int i = nextCoord[0]; i <= curCoord[0]; i ++) {
                            this.updateCells("explored", i, curCoord[1]);
                            this.updateCells("explored", i, curCoord[1] - 1);
                        }
                    }
                    break;
            }
        }
        this.setCurCoord(nextCoord[0], nextCoord[1], robotDirection);
    }
    public boolean validMove(int[] robotCoord, String direction) {
        ArrayList<int[]> obstacleCoords = this.getObstacleCoord();
        // examine for each obstacle on the map
        for (int[] currentObstacle : obstacleCoords) {
            int obstacleX = currentObstacle[0];
            int obstacleY = currentObstacle[1];

            /*
            manual way to check if robot is sitting on the obstacle
            since robot coordinate is based on the cell occupied by its top left wheel,
            depending on the direction, the cells to be examined are different
             */
            switch (direction) {
                case "up":
                    if (robotCoord[1] - 1 <= obstacleY && obstacleY <= robotCoord[1]
                            && robotCoord[0] <= obstacleX && obstacleX <= robotCoord[0] + 1) {
                        return false;
                    }
                    break;
                case "down":
                    if (robotCoord[1] <= obstacleY && obstacleY <= robotCoord[1] + 1
                            && robotCoord[0] - 1 <= obstacleX && obstacleX <= robotCoord[0]) {
                        return false;
                    }
                    break;
                case "left":
                    if (robotCoord[0] <= obstacleX && obstacleX <= robotCoord[0] + 1
                            && robotCoord[1] <= obstacleY && obstacleY <= robotCoord[1] + 1) {
                        return false;
                    }
                    break;
                case "right":
                    if (robotCoord[0] - 1 <= obstacleX && obstacleX <= robotCoord[0]
                            && robotCoord[1] - 1 <= obstacleY && obstacleY <= robotCoord[1]) {
                        return false;
                    }
                    break;
                default:
                    throw new IllegalArgumentException("Invalid direction: " + direction);
            }
        }
        return true;
    }

    private static class MyDragShadowBuilder extends DragShadowBuilder {
        private Point mScaleFactor;

        // Defines the constructor for myDragShadowBuilder
        public MyDragShadowBuilder(View v) {
            // Stores the View parameter passed to myDragShadowBuilder.
            super(v);
        }
        @Override
        public void onProvideShadowMetrics (Point size, Point touch) {
            // Defines local variables
            int width;
            int height;

            // Sets the width of the shadow to half the width of the original View
            width = (int) (cells[1][1].endX - cells[1][1].startX);

            // Sets the height of the shadow to half the height of the original View
            height = (int) (cells[1][1].endY - cells[1][1].startY);

            // Sets the size parameter's width and height values. These get back to the system
            // through the size parameter.
            size.set(width, height);
            // Sets size parameter to member that will be used for scaling shadow image.
            mScaleFactor = size;

            // Sets the touch point's position to be in the middle of the drag shadow
            touch.set(width / 2, height / 2);
        }

        @Override
        public void onDrawShadow(Canvas canvas) {
            // Draws the ColorDrawable in the Canvas passed in from the system.
            canvas.scale(mScaleFactor.x/(float)getView().getWidth(),
                    mScaleFactor.y/(float)getView().getHeight());
            getView().draw(canvas);
        }

    }

    public String getAllObstacles() {
        StringBuilder message = new StringBuilder();
        for (int i = 0; i < this.getObstacleCoord().size(); i ++) {
            int[] currentObstacle = this.getObstacleCoord().get(i);
            String imageBearing = IMAGE_BEARING[currentObstacle[1] - 1][currentObstacle[0] - 1];

            message.append(currentObstacle[0]).append(",").append(currentObstacle[1])
                    .append(",").append(imageBearing.charAt(0)).append(",")
                    .append(currentObstacle[2]).append("|");
        }
        return message.toString();
    }
    public void updateImageID(String obstacleID, String imageID) {
        int x = -1;     // x-cordinate (also the column)
        int y = -1;     // y-cordinate (also the row)
        for (int i = 0; i < this.getObstacleCoord().size(); i ++) {
            /*
            currentObstacle is a int[3] array
            currentObstacle[0] is the x-coord of the obstacle
            currentObstacle[1] is the y-coord of the obstacle
            currentObstacle[2] is the obstacle ID (with "OB" stripped) of the obstacle
             */
            int[] currentObstacle = this.getObstacleCoord().get(i);
            if (Integer.parseInt(obstacleID) == currentObstacle[2]) {
                x = currentObstacle[0];
                y = currentObstacle[1];
                this.setImageID(imageID, x, y);
            }
        }
        this.invalidate();
    }
    public void setImageID(String imageID, int x, int y) {
        IMAGE_LIST[y - 1][x - 1] = imageID;
    }

    public void setObstacleID(String obstacleID, int x, int y) {
        OBSTACLE_LIST[y - 1][x - 1] = obstacleID;
    }

    public void setImageBearing(String imageBearing, int x, int y) {
        IMAGE_BEARING[y - 1][x - 1] = imageBearing;
    }

    public void updateCells(String type, int x, int y) {
        cells[x][ROW - y].setType(type);
    }
    public String getObstacleID(int x, int y) {
        return OBSTACLE_LIST[y - 1][x - 1];
    }

    public String getImageID(int x, int y) {
        return IMAGE_LIST[y - 1][x - 1];
    }

    public String getImageBearing(int x, int y) {
        return IMAGE_BEARING[y - 1][x - 1];
    }
}