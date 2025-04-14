/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Asset } from './Asset';
/**
 * Mapping from ledger → exchange → list of assets
 */
export type LedgerExchangeAssetMap = Record<string, Record<string, Array<Asset>>>;
