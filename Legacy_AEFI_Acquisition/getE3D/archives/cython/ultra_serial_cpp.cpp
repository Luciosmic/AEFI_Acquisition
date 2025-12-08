#include <windows.h>
#include <iostream>
#include <chrono>
#include <string>
#include <vector>

class UltraSerialCpp {
private:
    HANDLE hSerial;
    std::string port_name;
    
public:
    UltraSerialCpp(const std::string& port = "COM10", DWORD baudrate = 1500000) {
        port_name = "\\\\.\\" + port;
        
        // Ouvrir le port série
        hSerial = CreateFileA(
            port_name.c_str(),
            GENERIC_READ | GENERIC_WRITE,
            0,
            NULL,
            OPEN_EXISTING,
            0,
            NULL
        );
        
        if (hSerial == INVALID_HANDLE_VALUE) {
            throw std::runtime_error("Erreur ouverture port série");
        }
        
        // Configuration du port
        DCB dcbSerialParams = {0};
        dcbSerialParams.DCBlength = sizeof(dcbSerialParams);
        
        if (!GetCommState(hSerial, &dcbSerialParams)) {
            CloseHandle(hSerial);
            throw std::runtime_error("Erreur GetCommState");
        }
        
        dcbSerialParams.BaudRate = baudrate;
        dcbSerialParams.ByteSize = 8;
        dcbSerialParams.StopBits = ONESTOPBIT;
        dcbSerialParams.Parity = NOPARITY;
        
        if (!SetCommState(hSerial, &dcbSerialParams)) {
            CloseHandle(hSerial);
            throw std::runtime_error("Erreur SetCommState");
        }
        
        // Timeouts (63ms comme optimisé)
        COMMTIMEOUTS timeouts = {0};
        timeouts.ReadIntervalTimeout = 0;
        timeouts.ReadTotalTimeoutConstant = 63;  // 63ms timeout
        timeouts.ReadTotalTimeoutMultiplier = 0;
        timeouts.WriteTotalTimeoutConstant = 10;
        timeouts.WriteTotalTimeoutMultiplier = 0;
        
        if (!SetCommTimeouts(hSerial, &timeouts)) {
            CloseHandle(hSerial);
            throw std::runtime_error("Erreur SetCommTimeouts");
        }
        
        // Vider les buffers
        PurgeComm(hSerial, PURGE_RXCLEAR | PURGE_TXCLEAR);
    }
    
    ~UltraSerialCpp() {
        if (hSerial != INVALID_HANDLE_VALUE) {
            CloseHandle(hSerial);
        }
    }
    
    std::pair<bool, double> ultra_fast_acquisition_m127() {
        auto start = std::chrono::high_resolution_clock::now();
        
        try {
            // Vider buffer
            PurgeComm(hSerial, PURGE_RXCLEAR);
            
            // Envoyer commande (pas de flush explicite)
            const char* command = "m127*";
            DWORD bytes_written = 0;
            
            if (!WriteFile(hSerial, command, 5, &bytes_written, NULL)) {
                auto end = std::chrono::high_resolution_clock::now();
                auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
                return {false, duration.count() / 1000.0};
            }
            
            // Lecture 1: confirmation (9 octets)
            char confirmation[10] = {0};
            DWORD bytes_read_1 = 0;
            if (!ReadFile(hSerial, confirmation, 9, &bytes_read_1, NULL)) {
                auto end = std::chrono::high_resolution_clock::now();
                auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
                return {false, duration.count() / 1000.0};
            }
            
            // Lecture 2: données réelles (99 octets)
            char real_data[100] = {0};
            DWORD bytes_read_2 = 0;
            if (!ReadFile(hSerial, real_data, 99, &bytes_read_2, NULL)) {
                auto end = std::chrono::high_resolution_clock::now();
                auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
                return {false, duration.count() / 1000.0};
            }
            
            auto end = std::chrono::high_resolution_clock::now();
            auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
            
            // Parsing simple : vérifier qu'on a des données valides
            std::string full_data = std::string(confirmation) + std::string(real_data);
            bool success = (bytes_read_1 == 9 && bytes_read_2 == 99 && full_data.find("m=  127") != std::string::npos);
            
            return {success, duration.count() / 1000.0};
            
        } catch (...) {
            auto end = std::chrono::high_resolution_clock::now();
            auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
            return {false, duration.count() / 1000.0};
        }
    }
};

int main() {
    std::cout << "=== TEST PERFORMANCE C++ PUR ===" << std::endl;
    
    try {
        UltraSerialCpp comm("COM10", 1500000);
        
        const int n_tests = 50;
        std::vector<double> times;
        int success_count = 0;
        
        std::cout << "Test avec " << n_tests << " acquisitions..." << std::endl;
        
        // Préchauffage
        for (int i = 0; i < 3; i++) {
            comm.ultra_fast_acquisition_m127();
            Sleep(10);
        }
        
        // Tests principaux
        for (int i = 0; i < n_tests; i++) {
            auto [success, duration_ms] = comm.ultra_fast_acquisition_m127();
            times.push_back(duration_ms);
            
            if (success) {
                success_count++;
            }
            
            Sleep(5);  // Petit délai entre acquisitions
        }
        
        // Calculs
        double total = 0;
        for (double t : times) total += t;
        double avg_time = total / times.size();
        
        double min_time = *std::min_element(times.begin(), times.end());
        double max_time = *std::max_element(times.begin(), times.end());
        double success_rate = (double)success_count / n_tests * 100.0;
        
        std::cout << "Temps moyen: " << avg_time << " ms" << std::endl;
        std::cout << "Temps min/max: " << min_time << "/" << max_time << " ms" << std::endl;
        std::cout << "Succès: " << success_rate << "%" << std::endl;
        
        // Comparaison
        double baseline_python = 140.0;
        double improvement = baseline_python / avg_time;
        std::cout << "Amélioration vs Python: " << improvement << "x plus rapide" << std::endl;
        
        if (avg_time < 100.0) {
            std::cout << "🎯 EXCELLENT: <100ms en C++ pur!" << std::endl;
        } else {
            std::cout << "Limite probablement matérielle: " << avg_time << "ms" << std::endl;
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Erreur: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
} 