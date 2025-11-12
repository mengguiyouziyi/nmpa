import OSS from 'ali-oss';
import dotenv from 'dotenv';


dotenv.config();

export const ossClient = new OSS({
  region: process.env.OSS_REGION,
  accessKeyId: process.env.OSS_ACCESS_KEY_ID,
  accessKeySecret: process.env.OSS_ACCESS_KEY_SECRET,
  bucket: process.env.OSS_BUCKET
});

export const uploadToOSS = async (localFilePath, ossPath) => {
    try {
      const result = await ossClient.put(ossPath, localFilePath);
      console.log(`OSS上传成功: ${ossPath}`);
      return result;
    } catch (err) {
      console.error(`OSS上传失败: ${err.message}`);
      throw err;
    }
  };


  