/*
 * Decompiled with CFR 0.153-SNAPSHOT (d6f6758-dirty).
 */
package rac;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.HashMap;
import javax.crypto.Cipher;
import javax.crypto.spec.SecretKeySpec;
import rac.CraftRiseCrypto;

public class AuthPayloadBuilder {
    public static String generateKey(String username, String password) {
        String passwordHash = CraftRiseCrypto.md5Hash(password);
        String original = username + "###" + passwordHash + "###" + System.currentTimeMillis();
        String base64Encoded = CraftRiseCrypto.base64Encode(original);
        String aesEncrypted1 = CraftRiseCrypto.encryptWithDefaultKey(base64Encoded);
        String aesEncrypted2 = CraftRiseCrypto.encryptWithDefaultKey(aesEncrypted1);
        String finalEncryptedKey = CraftRiseCrypto.base64Encode(aesEncrypted2);
        return finalEncryptedKey;
    }

    public static String b64(String s) {
        return Base64.getEncoder().encodeToString(s.getBytes(StandardCharsets.UTF_8));
    }

    public static String encrypt(String plainText) {
        try {
            SecretKeySpec keySpec = new SecretKeySpec("2650053489059452".getBytes(StandardCharsets.UTF_8), "AES");
            Cipher cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");
            cipher.init(1, keySpec);
            byte[] encryptedBytes = cipher.doFinal(plainText.getBytes(StandardCharsets.UTF_8));
            return Base64.getEncoder().encodeToString(encryptedBytes);
        } catch (Exception e) {
            e.printStackTrace();
            return "";
        }
    }

    public static String hash(String input, String algorithm) {
        try {
            MessageDigest digest = MessageDigest.getInstance(algorithm);
            byte[] hashBytes = digest.digest(input.getBytes());
            StringBuilder sb = new StringBuilder();
            for (byte b : hashBytes) {
                sb.append(String.format("%02x", b & 0xFF));
            }
            return sb.toString();
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    public static String md5Hash(String input) {
        return AuthPayloadBuilder.hash(input, "MD5");
    }

    public static HashMap<String, String> buildPayload(String username, String password) {
        HashMap<String, String> hashMap = new HashMap<String, String>();
        try {
            String key = AuthPayloadBuilder.generateKey(username, password);
            hashMap.put("key", key);
        } catch (Exception e) {
            e.printStackTrace();
            hashMap.put("key", "");
        }
        try {
            String sum = AuthPayloadBuilder.md5Hash((String)hashMap.get("key"));
            hashMap.put("sum", sum != null ? sum : "");
        } catch (Exception e) {
            e.printStackTrace();
            hashMap.put("sum", "");
        }
        try {
            String sumBig = AuthPayloadBuilder.md5Hash((String)hashMap.get("sum") + username + ".....");
            hashMap.put("sumBig", sumBig != null ? sumBig : "");
        } catch (Exception e) {
            e.printStackTrace();
            hashMap.put("sumBig", "");
        }
        try {
            String sumBigX = AuthPayloadBuilder.md5Hash("......" + (String)hashMap.get("sumBig") + "......");
            hashMap.put("sumBigX", sumBigX != null ? sumBigX : "");
        } catch (Exception e) {
            e.printStackTrace();
            hashMap.put("sumBigX", "");
        }
        try {
            String sumBigY = AuthPayloadBuilder.md5Hash("craftrise#" + username);
            hashMap.put("sumBigY", sumBigY != null ? sumBigY : "");
        } catch (Exception e) {
            e.printStackTrace();
            hashMap.put("sumBigY", "");
        }
        return hashMap;
    }
}

