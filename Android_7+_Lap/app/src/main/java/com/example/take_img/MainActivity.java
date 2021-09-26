package com.example.take_img;

import android.Manifest;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.drawable.BitmapDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.annotation.RequiresApi;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import com.squareup.picasso.Picasso;
import com.theartofdev.edmodo.cropper.CropImage;

import java.io.File;
import java.io.FileOutputStream;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.ProgressDialog;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.PorterDuff;
import android.media.Image;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.util.DisplayMetrics;
import android.util.Log;
import android.util.Size;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.widget.ImageView;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.ViewFlipper;


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

public class MainActivity extends AppCompatActivity {

    ImageView userpic;
    private static final int GalleryPick = 1;
    private static final int CAMERA_REQUEST = 100;
    private static final int STORAGE_REQUEST = 200;
    private static final int IMAGEPICK_GALLERY_REQUEST = 300;
    private static final int IMAGE_PICKCAMERA_REQUEST = 400;
    String cameraPermission[];
    String storagePermission[];
    Uri imageuri;
    int cameraHeight, cameraWidth, xOffset, yOffset, boxWidth, boxHeight;

    private String[] permissions = new String[]{
            Manifest.permission.INTERNET,
            Manifest.permission.READ_EXTERNAL_STORAGE,
            Manifest.permission.WRITE_EXTERNAL_STORAGE,
            Manifest.permission.CAMERA
    };

    private static final String encryptionKey           = "This is a key123";
    private static final String characterEncoding       = "UTF-8";
    private static final String cipherTransformation    = "AES/CBC/PKCS5PADDING";
    private static final String aesEncryptionAlgorithem = "AES";

    TextView click;

    Button saveimage;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Context context;
        // Here we are initialising
        // the text and image View
        click = findViewById(R.id.click);
        userpic = findViewById(R.id.imageview);
        //R.id.cropImageView

        saveimage = (Button)findViewById(R.id.savegallery);

        ActivityCompat.requestPermissions(MainActivity.this, new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, 1);
        ActivityCompat.requestPermissions(MainActivity.this, new String[]{Manifest.permission.READ_EXTERNAL_STORAGE}, 1);

        saveimage.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                //saveToGallery();
                DisplayMetrics displaymetrics = new DisplayMetrics();
                Bitmap bmp=saveToGallery();

                //Creating new cropped bitmap
                Bitmap bitmap = Bitmap.createScaledBitmap(bmp, 512, 512, false);
                saveImageToExternalStorage(bitmap);
                ViewFlipper vf = (ViewFlipper) findViewById( R.id.viewFlipper );
                ImageView imageView = (ImageView) findViewById(R.id.image1);
                imageView.setImageBitmap(bitmap);
                vf.showNext();
            }
        });

        // allowing permissions of gallery and camera
        cameraPermission = new String[]{Manifest.permission.CAMERA, Manifest.permission.WRITE_EXTERNAL_STORAGE};
        storagePermission = new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE};

        // After clicking on text we will have
        // to choose whether to
        // select image from camera and gallery
        click.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                showImagePicDialog();
            }
        });
    }

    private void showImagePicDialog() {
        String options[] = {"Camera", "Gallery"};
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("Pick Image From");
        builder.setItems(options, new DialogInterface.OnClickListener() {
            @RequiresApi(api = Build.VERSION_CODES.M)
            @Override
            public void onClick(DialogInterface dialog, int which) {
                if (which == 0) {
                    if (!checkCameraPermission()) {
                        requestCameraPermission();
                    } else {
                        pickFromGallery();
                    }
                } else if (which == 1) {
                    if (!checkStoragePermission()) {
                        requestStoragePermission();
                    } else {
                        pickFromGallery();
                    }
                }
            }
        });
        builder.create().show();
    }

    private Bitmap saveToGallery(){
        BitmapDrawable draw = (BitmapDrawable) userpic.getDrawable();
        Bitmap bmp = draw.getBitmap();
        File storageLoc = Environment.getExternalStorageDirectory();
        String filename = String.format("%d", System.currentTimeMillis());
        File file = new File(storageLoc, filename +".jpg");
        try
        {
            FileOutputStream fos = new FileOutputStream(file);
            bmp.compress(Bitmap.CompressFormat.JPEG, 100, fos);
            fos.close();
            return bmp;
        } catch(Exception e)
        {
         e.printStackTrace();
        }
        return bmp;
    }

    private void saveImageToExternalStorage(Bitmap finalBitmap) {
        String root = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES).toString();
        File myDir = new File(root + "/saved_images");
        myDir.mkdirs();
        Random generator = new Random();
        int n = 10000;
        n = generator.nextInt(n);
        String fname = "Image-" + n + ".jpg";
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

    private void uploadFile(File file) {
        // create upload service client
        FileUploadService service = ServiceGenerator.createService(FileUploadService.class);

        try {
            Uri fileUri = Uri.fromFile(file);
            // create RequestBody instance from file
            RequestBody requestFile = RequestBody.create(MediaType.parse("image/png"), file);

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
                    JsonObject result = response.body().getAsJsonObject();
                    String description = result.get("description").getAsString();
                    String price11 = result.get("price11").getAsString();
                    String price12 = result.get("price12").getAsString();
                    String price21 = result.get("price21").getAsString();
                    String price22 = result.get("price22").getAsString();
                    String barcode = result.get("barcode_data").getAsString();
                    String price_num_card = result.get("price_num_card").getAsString();
                    String price_num_nocard = result.get("price_num_nocard").getAsString();
                    String Type = result.get("Type").getAsString();
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
                            price_num_nocard + '\n' + "Ед. измерения: " + Type);
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

    // checking storage permissions
    private Boolean checkStoragePermission() {
        boolean result = ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE) == (PackageManager.PERMISSION_GRANTED);
        return result;
    }

    // Requesting  gallery permission
    @RequiresApi(api = Build.VERSION_CODES.M)
    private void requestStoragePermission() {
        requestPermissions(storagePermission, STORAGE_REQUEST);
    }

    // checking camera permissions
    private Boolean checkCameraPermission() {
        boolean result = ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == (PackageManager.PERMISSION_GRANTED);
        boolean result1 = ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE) == (PackageManager.PERMISSION_GRANTED);
        return result && result1;
    }

    // Requesting camera permission
    @RequiresApi(api = Build.VERSION_CODES.M)
    private void requestCameraPermission() {
        requestPermissions(cameraPermission, CAMERA_REQUEST);
    }

    // Requesting camera and gallery
    // permission if not given
    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        switch (requestCode) {
            case CAMERA_REQUEST: {
                if (grantResults.length > 0) {
                    boolean camera_accepted = grantResults[0] == PackageManager.PERMISSION_GRANTED;
                    boolean writeStorageaccepted = grantResults[1] == PackageManager.PERMISSION_GRANTED;
                    if (camera_accepted && writeStorageaccepted) {
                        pickFromGallery();
                    } else {
                        Toast.makeText(this, "Please Enable Camera and Storage Permissions", Toast.LENGTH_LONG).show();
                    }
                }
            }
            break;
            case STORAGE_REQUEST: {
                if (grantResults.length > 0) {
                    boolean writeStorageaccepted = grantResults[0] == PackageManager.PERMISSION_GRANTED;
                    if (writeStorageaccepted) {
                        pickFromGallery();
                    } else {
                        Toast.makeText(this, "Please Enable Storage Permissions", Toast.LENGTH_LONG).show();
                    }
                }
            }
            break;
        }
    }

    // Here we will pick image from gallery or camera
    private void pickFromGallery() {
        CropImage.activity().start(MainActivity.this);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == CropImage.CROP_IMAGE_ACTIVITY_REQUEST_CODE) {
            CropImage.ActivityResult result = CropImage.getActivityResult(data);
            if (resultCode == RESULT_OK) {
                Uri resultUri = result.getUri();
                Picasso.with(this).load(resultUri).into(userpic);
            }
        }
    }
}