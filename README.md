From this website: https://splunksearch.dell.com/en-US/app/search/search
Enter a search query: index="esupp_nginx" url="support/order-status/" cookie_dellcemsession="{Global_DellCEMSessionCookie_CSH}"
for each corresponding order number whose session has been going on. It should dynamically search the splunk for the last 7 days. then read all the data and then feed the data to the llm which only filters out the possible reason for the dsat and store this splunk exceptions in a new column of the output excel.
