### Simulate the beer simulation game in simpy. Assume each time step corre- sponds to one week. 

Consider the supply chain that is similar to what you played in in the game.

**Retailer → Wholesaler → Distributor → Factory.**

Assume a lead time that has a uniform distribution between one and four weeks. (The lead time can be one, two , three or four weeks with equal probability). This lead time exists between all entities.
Assume the customer demand is 100k with probability 15%, 150k with probability 15% and 200k with probability 70 %. The cost of holding a case is 0.5 $ and cost of missing an order is 1$. For each entity in the chain, assume the algorithm used to calculate the demand if is similar to the newsvendor problem.
Run the game for 50 time steps.
For the above game, submit the following: -

- 1. Plot the weekly costs of each entity as a function of time. 
- 2. Plot the inventory as a function of time.
- 3. Plot the orders placed by each entity a function of time.