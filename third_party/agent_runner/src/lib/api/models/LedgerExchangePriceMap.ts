/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Price } from './Price';
/**
 * Mapping from ledger → exchange → list of prices
 */
export type LedgerExchangePriceMap = Record<string, Record<string, Array<Price>>>;
