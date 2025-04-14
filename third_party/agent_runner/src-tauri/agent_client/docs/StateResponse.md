# StateResponse

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**portfolio** | Option<[**std::collections::HashMap<String, std::collections::HashMap<String, Vec<models::Asset>>>**](std::collections::HashMap.md)> | Mapping from ledger → exchange → list of assets | [optional]
**prices** | Option<[**std::collections::HashMap<String, std::collections::HashMap<String, Vec<models::Price>>>**](std::collections::HashMap.md)> | Mapping from ledger → exchange → list of prices | [optional]
**new_orders** | Option<[**Vec<serde_json::Value>**](serde_json::Value.md)> |  | [optional]
**open_orders** | Option<[**Vec<models::Order>**](Order.md)> |  | [optional]
**failed_orders** | Option<[**Vec<serde_json::Value>**](serde_json::Value.md)> |  | [optional]
**submitted_orders** | Option<[**Vec<serde_json::Value>**](serde_json::Value.md)> |  | [optional]
**unaffordable_opportunity** | Option<[**Vec<serde_json::Value>**](serde_json::Value.md)> |  | [optional]
**total_open_orders** | Option<**i32**> |  | [optional]
**time_since_last_update** | Option<**String**> |  | [optional]
**current_state** | Option<**String**> |  | [optional]
**current_period** | Option<**i32**> |  | [optional]
**is_healthy** | Option<**bool**> |  | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


