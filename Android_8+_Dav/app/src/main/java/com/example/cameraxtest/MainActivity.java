package com.example.cameraxtest;
import android.Manifest;
import android.app.ProgressDialog;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.PorterDuff;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.util.DisplayMetrics;
import android.util.Log;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.ViewFlipper;
import androidx.appcompat.app.AppCompatActivity;
import androidx.camera.core.Camera;
import androidx.camera.core.CameraSelector;
import androidx.camera.core.Preview;
import androidx.camera.lifecycle.ProcessCameraProvider;
import androidx.camera.view.PreviewView;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.lifecycle.LifecycleOwner;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.gson.JsonObject;
import java.io.File;
import java.io.FileOutputStream;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Random;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class MainActivity extends AppCompatActivity implements SurfaceHolder.Callback {
    PreviewView mCameraView;
    SurfaceHolder holder;
    SurfaceView surfaceView;
    Canvas canvas;
    Paint paint;
    int xOffset, yOffset, boxWidth, boxHeight;
    private static final String encryptionKey           = "This is a key123";
    private static final String characterEncoding       = "UTF-8";
    private static final String cipherTransformation    = "AES/CBC/PKCS5PADDING";
    private static final String aesEncryptionAlgorithem = "AES";
    private ListenableFuture<ProcessCameraProvider> cameraProviderFuture;
    private ExecutorService executor = Executors.newSingleThreadExecutor();

    private String[] permissions = new String[]{
                Manifest.permission.INTERNET,
                Manifest.permission.READ_EXTERNAL_STORAGE,
                Manifest.permission.WRITE_EXTERNAL_STORAGE,
                Manifest.permission.CAMERA
    };

    private boolean checkPermissions() {
        int result;
        List<String> listPermissionsNeeded = new ArrayList<>();
        for (String p : permissions) {
            result = ContextCompat.checkSelfPermission(this, p);
            if (result != PackageManager.PERMISSION_GRANTED) {
                listPermissionsNeeded.add(p);
            }
        }
        if (!listPermissionsNeeded.isEmpty()) {
            ActivityCompat.requestPermissions(this, listPermissionsNeeded.toArray(new String[listPermissionsNeeded.size()]), 100);
            return false;
        }
        return true;
    }
    /*
     * Starting Camera
     */
    void startCamera(){
        mCameraView = findViewById(R.id.previewView);
        cameraProviderFuture = ProcessCameraProvider.getInstance(this);
        cameraProviderFuture.addListener(new Runnable() {
            @Override
            public void run() {
                try {
                    ProcessCameraProvider cameraProvider = cameraProviderFuture.get();
                    MainActivity.this.bindPreview(cameraProvider);
                } catch (ExecutionException | InterruptedException e) {
                    // No errors need to be handled for this Future.
                    // This should never be reached.
                }
            }
        }, ContextCompat.getMainExecutor(this));
    }
    /*
     * Binding to camera
     */
    private void bindPreview(ProcessCameraProvider cameraProvider) {
        Preview preview = new Preview.Builder()
                .build();
        CameraSelector cameraSelector = new CameraSelector.Builder()
                .requireLensFacing(CameraSelector.LENS_FACING_BACK)
                .build();
        preview.setSurfaceProvider(mCameraView.createSurfaceProvider());
        Camera camera = cameraProvider.bindToLifecycle((LifecycleOwner)this, cameraSelector, preview);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        checkPermissions();
        setContentView(R.layout.activity_main);
        //Start Camera
        startCamera();
        //Create the bounding box
        surfaceView = findViewById(R.id.overlay);
        surfaceView.setZOrderOnTop(true);
        holder = surfaceView.getHolder();
        holder.setFormat(PixelFormat.TRANSPARENT);
        holder.addCallback(this);
    }

    /*
     * For drawing the rectangular box
     */
    private void DrawFocusRect(int color) {
        DisplayMetrics displaymetrics = new DisplayMetrics();
        getWindowManager().getDefaultDisplay().getMetrics(displaymetrics);
        int height = mCameraView.getHeight(); //4000
        int width = mCameraView.getWidth(); //3000
        int left, right, top, bottom, diameter;
        diameter = width; //3000
        if (height < width) {
            diameter = height;
        }
        int offset = (int) (0.05 * diameter); //150
        diameter -= offset; //2850
        canvas = holder.lockCanvas();
        canvas.drawColor(0, PorterDuff.Mode.CLEAR);
        //border's properties
        paint = new Paint();
        paint.setStyle(Paint.Style.STROKE);
        paint.setColor(color);
        paint.setStrokeWidth(5);
        left = width / 2 - diameter / 2; //75
        top = height / 2 - diameter / 2; //575
        right = width / 2 + diameter / 2; //2925
        bottom = height / 2 + diameter / 2; //3425
        xOffset = left;
        yOffset = top;
        boxHeight = bottom - top; //2850
        boxWidth = right - left; //2850
        //Changing the value of x in diameter/x will change the size of the box ; inversely proportionate to x
        canvas.drawRect(left, top, right, bottom, paint);
        holder.unlockCanvasAndPost(canvas);
    }
    /*
     * Callback functions for the surface Holder
     */
    @Override
    public void surfaceCreated(SurfaceHolder holder) {

    }

    @Override
    public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) {
        //Drawing rectangle
        DrawFocusRect(Color.parseColor("#b3dabb"));
    }

    @Override
    public void surfaceDestroyed(SurfaceHolder holder) {

    }

    public void capturing(View view) {
        Bitmap bmp=mCameraView.getBitmap();
        //Getting the values for cropping
        DisplayMetrics displaymetrics = new DisplayMetrics();
        getWindowManager().getDefaultDisplay().getMetrics(displaymetrics);
        int height = bmp.getHeight(); //4000
        int width = bmp.getWidth(); //3000
        int left, top, diameter;
        diameter = width;
        if (height < width) {
            diameter = height;
        }
        int offset = (int) (0.05 * diameter);
        diameter -= offset;
        left = width / 2 - diameter / 2;
        top = height / 2 - diameter / 2;
        xOffset = left;
        yOffset = top;
        //Creating new cropped bitmap
        Bitmap bitmap = Bitmap.createBitmap(bmp, left, top, boxWidth, boxHeight);
        saveImageToExternalStorage(bitmap);
        ViewFlipper vf = (ViewFlipper) findViewById( R.id.viewFlipper );
        ImageView imageView = (ImageView) findViewById(R.id.image1);
        imageView.setImageBitmap(bitmap);
        vf.showNext();
    }

    private void uploadFile(File file) {
        // create upload service client
        FileUploadService service =
                ServiceGenerator.createService(FileUploadService.class);
        try {
            Uri fileUri = Uri.fromFile(file);
            // create RequestBody instance from file
            RequestBody requestFile =
                    RequestBody.create(
                            MediaType.parse("image/png"),
                            file
                    );
            // MultipartBody.Part is used to send also the actual file name
            MultipartBody.Part body =
                    MultipartBody.Part.createFormData("picture", file.getName(), requestFile);
            // add another part within the multipart request
            String descriptionString = "hello, this is description speaking";
            RequestBody description =
                    RequestBody.create(
                            okhttp3.MultipartBody.FORM, descriptionString);
            // finally, execute the request
            Call<JsonObject> call = service.upload(description, body);
            TextView tw = (TextView) findViewById( R.id.resulttext );
            // Set up progress before call
            ProgressDialog nDialog;
            nDialog = new ProgressDialog(MainActivity.this);
            nDialog.setMessage("Loading..");
            nDialog.setTitle("Uploading to server");
            nDialog.setIndeterminate(false);
            nDialog.setCancelable(true);
            nDialog.show();
            call.enqueue(new Callback<JsonObject>() {
                @Override
                public void onResponse(Call<JsonObject> call,
                                       Response<JsonObject> response) {
                    Log.v("Upload", "success");
                    nDialog.dismiss();
                    //tw.setText(response.body().toString());
                    JsonObject result = response.body().getAsJsonObject();
                    String description = result.get("description").getAsString();
                    String price11 = result.get("price11").getAsString();
                    String price12 = result.get("price12").getAsString();
                    String price21 = result.get("price21").getAsString();
                    String price22 = result.get("price22").getAsString();
                    String barcode = result.get("barcode_data").getAsString();
                    String price_num_card = result.get("price_num_card").getAsString();
                    String price_num_nocard = result.get("price_num_nocard").getAsString();
                    String Type = result.get("type").getAsString();
                    String numType = result.get("numType").getAsString();
                    /*
                    tw.setText("Описание: " + decrypt(description) + '\n' + "Цена без карты: " +
                            decrypt(price11) + '.' + decrypt(price21) + '\n' + "Цена по карте: " +
                            decrypt(price22) + '.' + decrypt(price12) + '\n' + "Штрих-код: " +
                            decrypt(barcode) + '\n' + "Цена за ед, карта: " +
                            decrypt(price_num_card) + '\n' + "Цена за ед, без карты: " +
                            decrypt(price_num_nocard) + '\n' + "Ед. измерения: " + decrypt(Type));
*/
                    tw.setText("Описание: " + description + '\n' + "Цена без карты: " +
                            price11 + '.' + price21 + '\n' + "Цена по карте: " +
                            price22 + '.' + price12 + '\n' + "Штрих-код: " +
                            barcode + '\n' + "Цена за ед, карта: " +
                            price_num_card + '\n' + "Цена за ед, без карты: " +
                            price_num_nocard + '\n' + "Ед. измерения: " + Type + '\n' +
                            "Количество: " + numType);
                }
                @Override
                public void onFailure(Call<JsonObject> call, Throwable t) {
                    Log.e("Upload error:", t.toString());
                    nDialog.dismiss();
                    tw.setText("Upload error");
                }
            });
        } catch (Throwable e) {
            // Several error may come out with file handling or DOM
            e.printStackTrace();
            Toast.makeText(this, "ERROR?", Toast.LENGTH_SHORT).show();
            return;
        }
    }
/*
    public static String decrypt(String encryptedText) {
        String decryptedText = "";
        try {
            Cipher cipher = Cipher.getInstance(cipherTransformation);
            byte[] key = encryptionKey.getBytes(characterEncoding);
            SecretKeySpec secretKey = new SecretKeySpec(key, aesEncryptionAlgorithem);
            IvParameterSpec ivparameterspec = new IvParameterSpec(key);
            cipher.init(Cipher.DECRYPT_MODE, secretKey, ivparameterspec);
            Base64.Decoder decoder = Base64.getDecoder();
            byte[] cipherText = decoder.decode(encryptedText.getBytes("UTF8"));
            decryptedText = new String(cipher.doFinal(cipherText), "UTF-8");
        } catch (Exception E) {
            System.err.println("decrypt Exception : "+E.getMessage());
        }
        return decryptedText;
    }
*/
    public void backing(View view) {
        ViewFlipper vf = (ViewFlipper) findViewById( R.id.viewFlipper );
        vf.showNext();
    }

    private void saveImageToExternalStorage(Bitmap finalBitmap) {
        String root = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES).toString();
        File myDir = new File(root + "/saved_images");
        myDir.mkdirs();
        String fname = "Image-Tag.jpg";
        File file = new File(myDir, fname);
        if (file.exists())
            file.delete();
        try {
            FileOutputStream out = new FileOutputStream(file);
            finalBitmap.compress(Bitmap.CompressFormat.JPEG, 90, out);
            out.flush();
            out.close();
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        try
        {
            uploadFile(new File(myDir, fname));
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }
}