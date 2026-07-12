/*
 * Decompiled with CFR 0.153-SNAPSHOT (d6f6758-dirty).
 */
package rac;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;
import javax.crypto.Cipher;
import javax.crypto.spec.SecretKeySpec;

public class CraftRiseCrypto {
    public static final String AES_KEY = "2640023187059250";

    public static String decryptWithDefaultKey(String base64Encrypted) {
        try {
            SecretKeySpec keySpec = new SecretKeySpec("2650053489059452".getBytes(StandardCharsets.UTF_8), "AES");
            Cipher cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");
            cipher.init(2, keySpec);
            byte[] decryptedBytes = cipher.doFinal(Base64.getDecoder().decode(base64Encrypted));
            return new String(decryptedBytes, StandardCharsets.UTF_8);
        } catch (Exception e) {
            e.printStackTrace();
            return "";
        }
    }

    public static String decodeObfuscatedString(String string) {
        if (string == null) {
            return null;
        }
        if ((string = CraftRiseCrypto.base64Decode(string)) == null) {
            return null;
        }
        if ((string = CraftRiseCrypto.base64Decode(string)) == null) {
            return null;
        }
        if (string.startsWith("3ebi2mclmAM7Ao2") && string.endsWith("KweGTngiZOOj9d6")) {
            String prefix = string.substring(0, 15);
            String suffix = string.substring(string.length() - 15);
            if (prefix.equals("3ebi2mclmAM7Ao2") && suffix.equals("KweGTngiZOOj9d6")) {
                String middle = string.substring(15, string.length() - 15);
                return CraftRiseCrypto.base64Decode(middle);
            }
        }
        return string;
    }

    public static String base64Decode(String str) {
        try {
            return new String(Base64.getDecoder().decode(str), StandardCharsets.UTF_8);
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    public static String base64Encode(String str) {
        return Base64.getEncoder().encodeToString(str.getBytes(StandardCharsets.UTF_8));
    }

    public static String base64Encode(byte[] bytes) {
        return Base64.getEncoder().encodeToString(bytes);
    }

    public static String decryptWithKey(String encryptedBase64, String aesKey) {
        try {
            SecretKeySpec key = new SecretKeySpec(aesKey.getBytes(StandardCharsets.UTF_8), "AES");
            Cipher cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");
            cipher.init(2, key);
            byte[] decryptedBytes = cipher.doFinal(Base64.getDecoder().decode(encryptedBase64));
            return new String(decryptedBytes, StandardCharsets.UTF_8);
        } catch (Exception e) {
            e.printStackTrace();
            return "";
        }
    }

    public static String encryptWithDefaultKey(String plainText) {
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

    public static String encodeCustomBase64(String input) {
        String startFake = "3ebi2mclmAM7Ao2";
        String endFake = "KweGTngiZOOj9d6";
        String base64Encoded = Base64.getEncoder().encodeToString(input.getBytes());
        return startFake + base64Encoded + endFake;
    }

    public static String decodeCleanBase64(String input) {
        String startFake = "3ebi2mclmAM7Ao2";
        String endFake = "KweGTngiZOOj9d6";
        if (input.startsWith(startFake) && input.endsWith(endFake)) {
            String base64Part = input.substring(startFake.length(), input.length() - endFake.length());
            byte[] decodedBytes = Base64.getDecoder().decode(base64Part);
            return new String(decodedBytes);
        }
        throw new IllegalArgumentException("Input beklenen fake stringlerle ba\u00felam\u00fdyor veya bitmiyor.");
    }

    public static String encryptWithLauncherKey(String plainText) {
        try {
            SecretKeySpec keySpec = new SecretKeySpec(AES_KEY.getBytes(StandardCharsets.UTF_8), "AES");
            Cipher cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");
            cipher.init(1, keySpec);
            byte[] encryptedBytes = cipher.doFinal(plainText.getBytes(StandardCharsets.UTF_8));
            return Base64.getEncoder().encodeToString(encryptedBytes);
        } catch (Exception e) {
            e.printStackTrace();
            return "";
        }
    }

    public static String decryptWithLauncherKey(String base64Encrypted) {
        try {
            SecretKeySpec keySpec = new SecretKeySpec(AES_KEY.getBytes(StandardCharsets.UTF_8), "AES");
            Cipher cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");
            cipher.init(2, keySpec);
            byte[] decryptedBytes = cipher.doFinal(Base64.getDecoder().decode(base64Encrypted));
            return new String(decryptedBytes, StandardCharsets.UTF_8);
        } catch (Exception e) {
            e.printStackTrace();
            return "";
        }
    }

    public static String flexibleDecryptWithKey(String encryptedBase64, String aesKey, int mode) {
        try {
            SecretKeySpec key = new SecretKeySpec(aesKey.getBytes(StandardCharsets.UTF_8), "AES");
            Cipher cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");
            cipher.init(mode, key);
            byte[] resultBytes = cipher.doFinal(Base64.getDecoder().decode(encryptedBase64));
            return new String(resultBytes, StandardCharsets.UTF_8);
        } catch (Exception e) {
            e.printStackTrace();
            return "";
        }
    }

    public static String encryptPlain(String plainText) throws Exception {
        String base64Encoded = CraftRiseCrypto.base64Encode(plainText);
        base64Encoded = CraftRiseCrypto.base64Encode(base64Encoded);
        base64Encoded = CraftRiseCrypto.base64Encode(base64Encoded);
        String withPrefixes = base64Encoded.replaceFirst("^", "3ebi2mclmAM7Ao2").replaceFirst("^", "KweGTngiZOOj9d6");
        byte[] key = AES_KEY.getBytes(StandardCharsets.UTF_8);
        SecretKeySpec secretKey = new SecretKeySpec(key, "AES");
        Cipher cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");
        cipher.init(1, secretKey);
        byte[] encryptedBytes = cipher.doFinal(withPrefixes.getBytes(StandardCharsets.UTF_8));
        if (encryptedBytes == null) {
            throw new Exception("encryptPlain: encryptedBytes null d\u00f6nd\u00fc");
        }
        return Base64.getEncoder().encodeToString(encryptedBytes);
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
        return CraftRiseCrypto.hash(input, "MD5");
    }

    public static String hash(byte[] input, String algorithm) {
        try {
            MessageDigest md = MessageDigest.getInstance(algorithm);
            byte[] messageDigest = md.digest(input);
            StringBuilder sb = new StringBuilder();
            for (byte b : messageDigest) {
                sb.append(String.format("%02x", b & 0xFF));
            }
            return sb.toString();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    public static String md5Hash(byte[] input) {
        return CraftRiseCrypto.hash(input, "MD5");
    }
}

