# P2P Network Simulation

This project simulates a peer-to-peer (P2P) network where peers interact to generate transactions, mine blocks, and maintain a blockchain ledger. The simulation aims to study the behavior of different types of peers in the network and analyze various network statistics.

## Overview

The simulation involves the following components:

- **Peers**: Each peer represents a node in the P2P network. Peers can be categorized based on their speed and CPU capabilities.

- **Transactions**: Peers generate transactions and broadcast them to their connected peers.

- **Blocks**: Peers mine blocks containing a set of transactions and add them to the blockchain.

- **Event Handling**: Events such as transaction generation, transaction reception, block mining, and block reception are handled by the simulation.

## Files

The project consists of the following files:

- `transaction.py`: Defines the `Transaction` class representing transactions in the network.
- `block.py`: Defines the `Block` class representing blocks in the blockchain.
- `peer.py`: Defines the `Peer` class representing peers in the network.
- `handler.py`: Defines event handling mechanisms and the `Handler` class.
- `helper.py`: Contains helper functions used in the simulation.
- `main.py`: Main script to run the simulation.
- `README.md`: This documentation file.
- `figures/`: Directory to store visualization figures.
- `logs/`: Directory to store logs generated during the simulation.

## Usage

To run the simulation, execute the `main.py` script. You can specify the simulation parameters such as the number of peers, percentage of slow peers, percentage of low CPU peers, and transaction interarrival time using command-line arguments.

Example:
python main.py --n 20 --z0 10 --z1 50 --txn-mean 8

This command will initiate a simulation with 20 peers, 10% slow peers, 50% low CPU peers, and an average transaction interarrival time of 8 units.

## Results

After running the simulation, the following results are generated:

- **Blockchain Visualization**: Visualizations of the blockchain for each peer are saved in the `figures/` directory.
- **Network Graph**: Visualization of the P2P network graph is saved as `network_graph.png`.
- **Network Statistics**: Network statistics such as the length of the longest chain, percentage of blocks mined by different types of peers, and branch lengths are printed to the console.

## Dependencies

The project relies on the following Python libraries:

- `numpy`
- `networkx`
- `matplotlib`

Make sure to install these dependencies using `pip` before running the simulation.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

