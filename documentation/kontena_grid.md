# Kontena Grid Monitoring

Monitor Kontena grid nodes.

Requirements:
- jq
- curl

## Usage

Item Syntax | Description | Units |
----------- | ----------- | ----- |
kontena.grid.discover[<MASTER_ADDRESS>, <ACCESS_TOKEN>, <GRID_NAME>] | Discover nodes in Kontena grid | |
kontena.grid.node.connected[<MASTER_ADDRESS>, <ACCESS_TOKEN>, <GRID_NAME>, {#NODE}] | Node connection status | true/false |
