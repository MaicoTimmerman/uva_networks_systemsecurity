/*  Networking and Security Assignment: Lab3
 *  lab3-task1-timmermanm.cc
 *
 *  Created on: Sept 01, 2013
 *      Author: Chariklis <c.pittaras@uva.nl>
 *
 *  ns-3 simulation source code template
 *  Copyright (C) 2013 Chariklis Pittaras
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

//Definition of NS_LOG identifier
NS_LOG_COMPONENT_DEFINE("lab3-task1-timmermanm");
//Definition of global variables
volatile uint32_t mBytesReceived = 0;


/**
 * Callback function used for counting received bytes
 */
void ReceivePacket(std::string context, Ptr<const Packet> p) {
    mBytesReceived += p->GetSize();
}

int main(int argc, char *argv[]) {

    // Define your Simulation parameters
    int delay = 50; //ms
    int speed = 5; //Mbps
    int max_rwin = 31250;
    uint16_t sinkPort = 8080;
    double startTime = 1.;
    double stopTime = 50.;
    Ptr<Node> clientNode;
    Ptr<Node> serverNode;
    Ipv4Address clientIPAddress;
    Ipv4Address serverIPAddress;
    DataRate sendRate = DataRate("5Mbps");

    // Enable logging at level INFO
    LogComponentEnable("lab3-task1-timmermanm", LOG_LEVEL_INFO);

    // Create network topology using NodeContainer class
    NS_LOG_INFO("Creating Nodes...");
    NodeContainer nodes;
    nodes.Create(2);
    serverNode = nodes.Get(0);
    clientNode = nodes.Get(1);

    // Install Internet Stack on nodes
    NS_LOG_INFO("Creating InternetStackHelper...");
    InternetStackHelper InetStack;
    InetStack.Install(nodes);

    // Create pointToPoint channel with specified data rate and delay,
    //without IP addresses first
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


    // Set the maximum receiving window size (RWIN)
    NS_LOG_INFO("Setting MaxWindowSize.");
    Config::SetDefault("ns3::TcpSocketBase::MaxWindowSize",
            UintegerValue(max_rwin));

    // Print the maximum receiving window size (RWIN)
    cout << " - Maximum receiving window: " << max_rwin << " bytes" << endl;

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
    cout << " - Server address: " << serverIPAddress << endl;
    cout << " - Client address: " << clientIPAddress << endl;


    // Create TCP applications installed on nodes.
    NS_LOG_INFO("Creating TCP applications...");


    // Create a packet sink on the server to receive packets.
    NS_LOG_INFO(" - Creating TCP server application...");
    Address serverSinkAddress(InetSocketAddress(serverIPAddress, sinkPort));
    PacketSinkHelper packetSinkHelper(
            "ns3::TcpSocketFactory", serverSinkAddress);

    ApplicationContainer serverApp = packetSinkHelper.Install(serverNode);
    serverApp.Start(Seconds(startTime));
    serverApp.Stop(Seconds(stopTime));


    // Create an OnOff client application to send TCP to the server.
    NS_LOG_INFO(" - Creating TCP client application...");
    OnOffHelper onOffHelper("ns3::TcpSocketFactory", serverSinkAddress);
    onOffHelper.SetAttribute("OnTime", StringValue(
                "ns3::ConstantRandomVariable[Constant=1]"));
    onOffHelper.SetAttribute("OffTime", StringValue(
                "ns3::ConstantRandomVariable[Constant=0]"));

    // Set the sending rate to 2Mbps
    onOffHelper.SetConstantRate(sendRate);

    AddressValue remoteAddress(InetSocketAddress(serverIPAddress, sinkPort));
    onOffHelper.SetAttribute("Remote", remoteAddress);

    ApplicationContainer clientApp = onOffHelper.Install(clientNode);
    clientApp.Start(Seconds(startTime));
    clientApp.Stop(Seconds(stopTime));

    // Enable ascii tracing, you can find the tcp-task1.tr file in the ns-3.17 directory
    NS_LOG_INFO("Setting up TCP package tracing...");
    AsciiTraceHelper ascii;
    point2Point.EnableAsciiAll(ascii.CreateFileStream("tcp-task1.tr"));


    // Hook up the callback function with the receiving packet event
    // of the node 0, device 1
    std::string ctx = "/NodeList/0/DeviceList/1/$ns3::PointToPointNetDevice/MacRx";
    Config::Connect(ctx, MakeCallback(&ReceivePacket));


    //Install FlowMonitor on all nodes
    NS_LOG_INFO("Creating FlowMonitor...");
    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll();


    //Set simulation timeout and run.
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

    for (std::map<FlowId, FlowMonitor::FlowStats>::const_iterator i = stats.begin();
            i != stats.end(); ++i)
    {
        Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(i->first);
        if ((t.destinationAddress == serverIPAddress))
        {
            std::cout << "Flow " << i->first << " (" << t.sourceAddress
                    << " -> " << t.destinationAddress << ")\n";
            std::cout << "Start running time: " << i->second.timeFirstTxPacket.GetSeconds() << endl;
            std::cout << "Stop running time:  " << i->second.timeLastRxPacket.GetSeconds() << endl;
            std::cout << " - Tx Bytes:   " << i->second.txBytes << "\n";
            std::cout << " - Rx Bytes:   " << i->second.rxBytes << "\n";
            std::cout << " - Throughput: " << i->second.rxBytes * 8.0
                    / (i->second.timeLastRxPacket.GetSeconds() - i->second.timeFirstTxPacket.GetSeconds())
                    / 1000 / 1000 << " Mbps\n";
        }
    }

    Simulator::Destroy();
    NS_LOG_INFO("\nDone.");
}
