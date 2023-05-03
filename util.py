import pandas as pd
import numpy as np

def add_list(lst1 , lst2):
    cumulative_list = []
    for i in range(len(lst1)):
        cumulative_list.append(int(lst1[i] + lst2[i]))
    return cumulative_list


def calculate_turnover(df , T, topn, moving_avg = False):
    
    if moving_avg == True:
        demand = df[df['type'] == 'OUT']
        supply = df[df['type'] == 'IN']

        # create a complete day_id for each product
        day = []
        for i in range(1, 308):
            day.append(i)

        product = []
        for i in range(1, 21):
            for j in range(1, 308):
                product.append(i)

        complete_date = pd.DataFrame({'day_id' : day * 20, 'product_id' : product})
        merged_demand = demand.merge(complete_date, on = ['day_id', 'product_id'], how = 'outer')
        merged_demand = merged_demand.sort_values(['product_id', 'day_id']).reset_index()
        merged_demand = merged_demand[['day_id', 'product_id', 'quantity']]

        # calculate the weekday for each data row
        merged_demand['weekday'] = merged_demand['day_id'] % 6
        merged_demand['week_id'] = (np.ceil(merged_demand['day_id'] / 6)).astype(int)
        merged_demand = merged_demand.fillna(0)

        # calculate the moving average. To concate the data, we rename the column name of moving average to quantity_new
        merged_demand['quantity_new'] = merged_demand.groupby(['product_id', 'weekday'])['quantity'].transform((lambda x: x.rolling(17, 17).mean())).values
        merged_demand['quantity_new'] = merged_demand.groupby(['product_id', 'weekday'])['quantity_new'].shift(1)
        merged_demand = merged_demand.fillna(0)
        merged_demand['type'] = 'OUT'
        merged_demand = merged_demand[['day_id', 'week_id', 'product_id', 'quantity', 'type', 'quantity_new']]
        # merged_demand.head(20)

        # final dataset
        merged_df = pd.concat([supply, merged_demand])
        merged_df = merged_df.sort_values(['product_id', 'day_id']).reset_index()
        merged_df = merged_df.drop('index', axis = 1)
    
        df = merged_df
    else:
        pass
    
    # add minus sign if the type is OUT
    df['quantity_new'] = np.where(df['type'] == 'IN', df['quantity'], df['quantity'] * -1)

    # calculate the net quantity
    calculate_net_quantity = df.groupby(['product_id', 'day_id', 'type'])['quantity_new'].sum()
    calculate_net_quantity = calculate_net_quantity.reset_index().sort_values(['day_id', 'product_id', 'type'])
    calculate_net_quantity['grand total'] = abs(calculate_net_quantity['quantity_new'])
    
    # calculate the turnover rate
    daily_turnover_rate = calculate_net_quantity[['day_id', 'product_id', 'grand total', 'quantity_new']]
    daily_turnover_rate = daily_turnover_rate.groupby(['product_id', 'day_id'])[['quantity_new', 'grand total']].sum()
    daily_turnover_rate['cummulative'] = daily_turnover_rate.groupby(['product_id'])['quantity_new'].cumsum()
    daily_turnover_rate = daily_turnover_rate.reset_index()
    
    # avoid turnover rate from being negative values
    daily_turnover_rate['turnover'] = daily_turnover_rate['grand total'] / (daily_turnover_rate['cummulative'] - daily_turnover_rate['cummulative'].min())
    
    # calculate the frequency based on T
    daily_turnover_rate['frequency'] = (np.ceil(daily_turnover_rate['day_id'] / T)).astype(int)
    daily_turnover_rate['week_id'] = (np.ceil(daily_turnover_rate['day_id'] / 6)).astype(int)
    
    # sort by frequency
    turnover_rate_series = daily_turnover_rate.groupby(['product_id', 'frequency'])['turnover'].sum() / T
    turnover_rate_df = turnover_rate_series.reset_index()
    result = daily_turnover_rate.merge(turnover_rate_df, on = ['product_id', 'frequency'])

    # select necessary columns
    result['IN'] = (result['grand total'] + result['quantity_new']) / 2
    result['OUT'] = (result['grand total'] - result['quantity_new']) / 2
    result = result[['product_id', 'frequency', 'day_id', 'IN', 'OUT', 'turnover_y', 'week_id']]
    
    # return topn product
    product_list = result['product_id'].unique()
    product_list = product_list[:topn]
    result = result[result['product_id'].isin(product_list)]
    
    return result


class product_object:
    def __init__(self, product_id , number_of_classes):
        self.number_of_classes = number_of_classes
        self.product_id = product_id
        self.current_inventory = [0] * (number_of_classes - 1) + [100000]###initiate starting inventory in all three classes
        self.class_log = [] ### initiate a list for storing all the class logs

    def update_storage_inbound(self , update_class_log):
        self.current_inventory = add_list(self.current_inventory , update_class_log)
        
    def update_storage_outbound(self , number_of_product_to_take):
        class_indexer = 0
        
        ### return a list of retrieval from each class
        retrieve_table = [0] * self.number_of_classes
        
        ### create temp # product to record how many left to retrieve
        number_of_product_to_retrieve = number_of_product_to_take
        
        while number_of_product_to_retrieve != 0:
            subtract = number_of_product_to_retrieve - self.current_inventory[class_indexer]
            
            ### if class has enough product to retrieve from
            if subtract <= 0:
                self.current_inventory[class_indexer] = self.current_inventory[class_indexer] - number_of_product_to_retrieve
                retrieve_table[class_indexer] = number_of_product_to_retrieve
                number_of_product_to_retrieve = 0
                break
    
            
            ### if class doesn't have enough product to retrieve from
            else:
                number_of_product_to_retrieve = number_of_product_to_retrieve - self.current_inventory[class_indexer]
                retrieve_table[class_indexer] = self.current_inventory[class_indexer]
                self.current_inventory[class_indexer] = 0 ### all retrieved
                class_indexer = class_indexer + 1
        
        return retrieve_table
            
            
        self.current_inventory = add_list(self.current_inventory , update_class_log * -1)
    
    def tenor_update(self , tenor_id , update_class_log):
        self.class_log.append([tenor_id , update_class_log])
            
    def print_all_class_logs(self):
        class_column = [str(f"Class {col_index}") for col_index in range(1 , self.number_of_classes)]
        class_column = class_column + 'Class backup'
        df = pd.DataFrame([log[1] for log in self.class_log] , column = class_column)
        df['tenor_index'] = [T[0] for T in self.class_log]
    
    def print_class_name(self):
        print(self.product_id)
        
    def print_current_inventory(self):
        print(self.current_inventory)


class class_object:
    def __init__(self, class_id , n_products , max_capacity = 984 , if_backup = False):
        self.class_id = class_id
        self.max_capacity = max_capacity
        self.current_inventory = np.zeros(n_products)
        self.current_capacity = 0
        
        ### create unlimited backup class
        if if_backup:
            self.current_inventory = [100000] * n_products
            self.max_capacity = 100000
            self.current_capacity = sum(self.current_inventory)
        


    ### Inbound handling 
    def stuff_product(self, product_index , number_of_product): 
        spare_room = self.max_capacity - self.current_capacity ### check room left
        product_index = int(product_index) ### convert index to int for indexing

        if spare_room >= number_of_product: ### if enough room
            self.current_inventory[product_index - 1] = self.current_inventory[product_index - 1] + number_of_product
            self.current_capacity = sum(self.current_inventory) ### update capacity
            return 0

        else: ### if not enough room
            self.current_inventory[product_index - 1] = self.current_inventory[product_index - 1] + spare_room ### stuff to max
            self.current_capacity = self.max_capacity ### update capacity
            return number_of_product - spare_room ### return number of products that are not stored
    
    ### Outbound handling
    def take_product(self , product_index , retrieval_count):
        self.current_inventory[product_index] = self.current_inventory[product_index] - retrieval_count
        self.current_capacity = sum(self.current_inventory)
        
    def return_numbers(self):
        print('current inventory :' , self.current_inventory)
        print('current capacity :' , self.current_capacity)



def supplychain_optimize(turnover_df , number_of_classes, number_of_products):
    
    ### initiate list of 4 classes
    class_object_list = []
    for i in range(1,5):
        class_object_list.append(class_object(f"{i}" , number_of_products))

    ### add one backup storage
    class_object_list.append(class_object(5 , number_of_products , if_backup = True))
    ### adjust for backup class
    number_of_classes = number_of_classes + 1


    ### initiate list of top ten products
    product_object_list = []
    for i in range(1,11):
        product_object_list.append(product_object(f"{i}" , number_of_classes))
    
    inbound_logs = []
    outbound_logs = []
    ### for each tenor data
    for tenor in list(turnover_df.groupby('frequency')):
        ### sort tenor data with day id and turnover
        tenor_df = tenor[1].sort_values(['day_id' , 'turnover_y'] , ascending = [True, False])
        ### tenor storing log
        tenor_storing_log_outbound = [[0] * number_of_classes] * number_of_products
        tenor_storing_log_inbound = [[0] * number_of_classes] * number_of_products

        ### for each log
        for index , row in tenor_df.iterrows():

            ### handle inbound
            storing_log = [0] * number_of_classes ### document all classes product i is stored
            number_of_product_to_store = row['IN'] ### number of product to store
            number_of_product_to_take = row['OUT'] ### number of product to take
            temp_product_count = number_of_product_to_store
            non_stored = number_of_product_to_store
            product_id = int(row['product_id']) - 1

            for class_index in range(len(class_object_list)): ### enumerate through all the classes to store
                ### try to store product into class
                non_stored = class_object_list[class_index].stuff_product(row['product_id'] , non_stored)
                class_i_stored = temp_product_count - non_stored
                storing_log[class_index] =  class_i_stored  ### record log

                ### if completely stored
                if non_stored == 0:
                    ### calculate row change log
                    temp_log = add_list(tenor_storing_log_inbound[product_id] , storing_log)
                    ### update product log
                    tenor_storing_log_inbound[product_id] = temp_log
                    ### update product object
                    product_object_list[product_id].update_storage_inbound(storing_log)
                    break

                ### if not enough storage
                else:
                    continue


            ### handle outbound
            if number_of_product_to_take == 0: ### if no outbound, go to next row
                continue
            else:
                ### table of what to retrieve from which table
                retrieve_table = product_object_list[product_id].update_storage_outbound(number_of_product_to_take)
                for index in range(len(retrieve_table)):
                    class_object_list[index].take_product(product_id , retrieve_table[index])

                ### update tenor_list
                tenor_storing_log_outbound[product_id] = add_list(tenor_storing_log_outbound[product_id] , retrieve_table)

        ### store all the logs
        inbound_logs.append(tenor_storing_log_inbound)
        outbound_logs.append(tenor_storing_log_outbound)
        
    return inbound_logs , outbound_logs
