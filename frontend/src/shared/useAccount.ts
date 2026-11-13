import { useSyncExternalStore } from 'react';
import { getAccount, subscribeAccount } from './account';
export function useAccount() { return useSyncExternalStore(subscribeAccount, getAccount); }
