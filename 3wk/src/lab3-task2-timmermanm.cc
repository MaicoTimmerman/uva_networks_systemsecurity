/*  Networking and System Security: Lab3
 *  lab3-task2-timmermanm.cc
 *
 *      Author: Chariklis <c.pittaras@uva.nl>
 * This file was created based on the  $NS3 HOME/examples/tutorial/fifth.cc
 *
 *  ns-3 simulation source code template
 *  Copyright (C) 2013 Canh Ngo
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/internet-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/ipv4-global-routing-helper.h"

using namespace ns3;
using namespace std;


class MyApp:
    public Application {
        public:
            MyApp();
            virtual ~MyApp();

            void Setup(
                    Ptr<Socket> socket,
                    Address address,
                    uint32_t packetSize,
                    DataRate dataRate
                    );
            void ChangeRate(DataRate newrate);

        private:
            virtual void StartApplication(void);
            virtual void StopApplication(void);

            void ScheduleTx(void);
            void SendPacket(void);

            Ptr<Socket> m_socket;
            Address m_peer;
            uint32_t m_packetSize;
            uint32_t m_nPackets;
            DataRate m_dataRate;
            EventId m_sendEvent;
            bool m_running;
            uint32_t m_packetsSent;
    };

MyApp::MyApp():
    m_socket(0),
    m_peer(),
    m_packetSize(0),
    m_dataRate(0),
    m_sendEvent(),
    m_running(false),
    m_packetsSent(0)
{}

MyApp::~MyApp() {
    m_socket = 0;
}

void MyApp::Setup(
        Ptr<Socket> socket,
        Address address,
        uint32_t packetSize,
        DataRate dataRate)
{
    m_socket = socket;
    m_peer = address;
    m_packetSize = packetSize;
    m_dataRate = dataRate;
}

void MyApp::StartApplication(void) {
    m_running = true;
    m_packetsSent = 0;
    m_socket->Bind();
    m_socket->Connect(m_peer);
    SendPacket();
}

void MyApp::StopApplication(void) {
    m_running = false;

    if (m_sendEvent.IsRunning()) {
        Simulator::Cancel(m_sendEvent);
    }

    if (m_socket) {
        m_socket->Close();
    }
}

void MyApp::SendPacket(void) {
    Ptr<Packet> packet = Create<Packet>(m_packetSize);
    m_socket->Send(packet);

    //  if (++m_packetsSent < m_nPackets)
    //    {
    ScheduleTx();
    //    }
}

void MyApp::ScheduleTx(void) {
    if (m_running) {
        Time tNext(Seconds(m_packetSize * 8 /
                    static_cast<double>(m_dataRate.GetBitRate())));
        m_sendEvent = Simulator::Schedule(tNext, &MyApp::SendPacket, this);
    }
}

void MyApp::ChangeRate(DataRate newrate) {
    m_dataRate = newrate;
    return;
}

/**
 * Callback function to handle CWND changes
 */
void CWndTracer(uint32_t oldCwnd, uint32_t newCwnd) {
    std::cout << Simulator::Now().GetSeconds() << "\t" << newCwnd << "\n";
}

//Definition of NS_LOG identifier
NS_LOG_COMPONENT_DEFINE("lab3-task2-timmermanm");

int main(int argc, char *argv[]) {
    //enable logging at level INFO
    LogComponentEnable ("lab3-task2-timmermanm", LOG_LEVEL_INFO);

    //Global configuration
    int delay = 20; //ms
    int speed = 2; //Mbps
    int droptailQueueSize = 20;
    uint16_t sinkPort = 8080;
    uint16_t tcpPacketSize = 1600;
    double serverStartTime = .5;
    double clientStartTime = 1.;
    double stopTime = 50.;
    // string tcpSocketType = "ns3::TcpNewReno";
    // string tcpSocketType = "ns3::TcpTahoe";
    string tcpSocketType = "ns3::TcpReno";

    Ptr<Node> clientNode;
    Ptr<Node> serverNode;
    Ipv4Address clientIPAddress;
    Ipv4Address serverIPAddress;
    DataRate tcpDataRate= DataRate("2Mbps");

    // Set the TCP Socket Type
    NS_LOG_INFO("Setting TCP socket type...");
    cout << " - TCP socket type: " << tcpSocketType << endl;
    Config::SetDefault("ns3::TcpL4Protocol::SocketType",
            StringValue(tcpSocketType));

    // Set disable of ACK
    NS_LOG_INFO("Disabling delayed ACK...");
    Config::SetDefault("ns3::TcpSocket::DelAckCount", UintegerValue(1));

    // Set DropTailQueue size when is needed
    NS_LOG_INFO("Setting Droptail queue size...");
    Config::SetDefault("ns3::DropTailQueue::MaxPackets",
            UintegerValue(droptailQueueSize));
    cout << " - Droptail Queue Size: " << droptailQueueSize <<
        " packets" << endl;

    // Create network topology using NodeContainer class
    NS_LOG_INFO("Creating nodes...");
    NodeContainer nodes;
    nodes.Create(2);
    serverNode = nodes.Get(0);
    clientNode = nodes.Get(1);

    // Install Internet Stack on nodes
    NS_LOG_INFO("Creating InternetStackHelper...");
    InternetStackHelper stack;
    stack.Install(nodes);

    // Create pointToPoint channel with specified data rate and delay,
    // without IP addresses first ...
    NS_LOG_INFO("Creating PointToPointHelper...");
    PointToPointHelper point2Point;

    NS_LOG_INFO("Setting DataRate...");
    std::stringstream ss_speed;
    ss_speed << "" << speed << "Mbps";
    point2Point.SetDeviceAttribute("DataRate", StringValue(ss_speed.str()));
    cout << " - DataRate: " << ss_speed.str() << endl;

    NS_LOG_INFO("Setting Delay...");
    std::stringstream ss_delay;
    ss_delay << "" << delay << "ms";
    point2Point.SetChannelAttribute("Delay", StringValue(ss_delay.str()));
    cout << " - Delay: " << ss_delay.str() << endl;


    // Install netDevices to the nodes
    NS_LOG_INFO("Creating NetDeviceContainer...");
    NetDeviceContainer devices;
    devices = point2Point.Install(nodes);

    // Assign IP addresses
    NS_LOG_INFO("Creating Ipv4AddressHelper...");
    Ipv4AddressHelper address;

    NS_LOG_INFO("Assigning Ipv4 Addresses...");
    address.SetBase("10.1.1.0", "255.255.255.252");
    Ipv4InterfaceContainer interfaces = address.Assign(devices);

    // Print here the server and client addresses
    serverIPAddress = interfaces.GetAddress(0);
    clientIPAddress = interfaces.GetAddress(1);
    cout << " - Server address : " << serverIPAddress << endl;
    cout << " - Client address : " << clientIPAddress << endl;

    // Create TCP applications installed on nodes.
    NS_LOG_INFO("Create TCP Applications.");

    // Create a packet sink on the server to receive packets.
    NS_LOG_INFO(" - Creating TCP server application...");
    Address serverSinkAddress(InetSocketAddress(serverIPAddress, sinkPort));
    PacketSinkHelper packetSinkHelper(
            "ns3::TcpSocketFactory", serverSinkAddress);

    ApplicationContainer serverApp = packetSinkHelper.Install(serverNode);
    serverApp.Start(Seconds(serverStartTime));
    serverApp.Stop(Seconds(stopTime));

    // Create a TCP client socket
    NS_LOG_INFO(" - Creating TCP client application...");
    Ptr<Socket> clientSocket = Socket::CreateSocket(clientNode,
            TcpSocketFactory::GetTypeId());

    // Monitor Congestion window
    clientSocket->TraceConnectWithoutContext("CongestionWindow",
            MakeCallback(&CWndTracer));

    // Create an application
    Ptr<MyApp> clientApp = CreateObject<MyApp>();


    // Bind socket to the application and connect to server with sending date
    // rate and packet size.  Note: the serverSinkAddress is an Address class
    // (include also port) and not an Ipv4Address
    clientApp->Setup(clientSocket, serverSinkAddress, tcpPacketSize,
            DataRate(tcpDataRate));

    // Install the application to the client node
    clientNode->AddApplication(clientApp);

    // Set start and stop running time of the app.
    clientApp->SetStartTime(Seconds(clientStartTime));
    clientApp->SetStopTime(Seconds(stopTime));

    // Enable ascii tracing, you can find the tcp-task2.tr file in the ns-3.17
    // directory
    AsciiTraceHelper ascii;
    point2Point.EnableAsciiAll(ascii.CreateFileStream("tcp-task2.tr"));

    // Install FlowMonitor on all nodes
    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll();

    // Set simulation timeout and run.
    NS_LOG_INFO("Starting simulation...\n");
    Simulator::Stop(Seconds(stopTime));
    Simulator::Run();

    /* measure the throughput.
     * For measuring the throughput we use the FlowMonitorHelper class.
     * see $NS3 HOME/examples/wireless/wifi-hidden-terminal.cc
     */
    monitor->CheckForLostPackets();
    Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(
            flowmon.GetClassifier());
    std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();
    for (std::map<FlowId, FlowMonitor::FlowStats>::const_iterator i =
            stats.begin(); i != stats.end(); ++i) {
        Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(i->first);
        /*if ((t.destinationAddress == udpServerAddress))*/ {
            std::cerr << "Flow " << i->first << " (" << t.sourceAddress
                << " -> " << t.destinationAddress << ")\n";
            std::cerr << "Start running time: " <<
                i->second.timeFirstTxPacket.GetSeconds() << endl;
            std::cerr << "Stop running time:  " <<
                i->second.timeLastRxPacket.GetSeconds() << endl;
            std::cerr << "  Tx Bytes:   " << i->second.txBytes << "\n";
            std::cerr << "  Rx Bytes:   " << i->second.rxBytes << "\n";
            std::cerr << "  Throughput: " << i->second.rxBytes * 8.0
                / (i->second.timeLastRxPacket.GetSeconds() -
                        i->second.timeFirstTxPacket.GetSeconds())
                / 1000 / 1000 << " Mbps\n";
        }
    }

    Simulator::Destroy();
    NS_LOG_INFO("\nDone.");
}
