package com.example.take_img;

import com.google.gson.JsonObject;

import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import retrofit2.Call;
import retrofit2.http.Multipart;
import retrofit2.http.POST;
import retrofit2.http.Part;

public interface FileUploadService {
    @Multipart
    @POST("upload")
    Call<JsonObject> upload(
            @Part("description") RequestBody description,
            @Part MultipartBody.Part file
    );
}
