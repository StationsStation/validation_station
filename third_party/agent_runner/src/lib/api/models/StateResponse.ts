/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LedgerExchangeAssetMap } from './LedgerExchangeAssetMap';
import type { LedgerExchangePriceMap } from './LedgerExchangePriceMap';
import type { Order } from './Order';
export type StateResponse = {
    portfolio?: LedgerExchangeAssetMap;
    prices?: LedgerExchangePriceMap;
    new_orders?: Array<any>;
    open_orders?: Array<Order>;
    failed_orders?: Array<any>;
    submitted_orders?: Array<any>;
    unaffordable_opportunity?: Array<any>;
    total_open_orders?: number;
    time_since_last_update?: string;
    current_state?: string;
    current_period?: number;
    is_healthy?: boolean;
};

