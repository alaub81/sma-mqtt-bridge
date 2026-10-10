#include <iostream>
#include <string>
#include "json.hpp"

int main(int argc, char* argv[]) {
    if (argc == 2 && std::string(argv[1]) == "--version") {
        std::cout << "sma-mqtt-bridge 0.0.0-bootstrap\n";
        return 0;
    }
    if (argc == 2 && (std::string(argv[1]) == "--help" || std::string(argv[1]) == "-h")) {
        std::cout << "Usage: sma_mqtt_bridge [--help | --version | --project-status]\n"
                  << "Project scaffold: SMA adapters and MQTT runtime are not implemented yet.\n";
        return 0;
    }
    if (argc == 2 && std::string(argv[1]) == "--project-status") {
        const nlohmann::json status = {
            {"stage", "bootstrap"},
            {"runtimeImplemented", false},
            {"plannedAdapters", {"inverter-modbus", "home-manager-meter", "echarger-local", "ennexos-portal"}},
            {"paidSmaApisRequired", false}
        };
        std::cout << status.dump() << '\n';
        return 0;
    }
    if (argc != 1) {
        std::cerr << "Unsupported command. Use --help.\n";
        return 64;
    }
    std::cerr << "SMA adapters and MQTT runtime are not implemented yet. "
              << "Read docs/IMPLEMENTATION_PLAN.md before starting the bridge.\n";
    return 78;
}
