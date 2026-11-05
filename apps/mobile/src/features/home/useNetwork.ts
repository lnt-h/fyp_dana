import NetInfo from '@react-native-community/netinfo';
import { useEffect, useState } from 'react';

/** True only when the device reports no connection (unknown reachability counts as online). */
export function useIsOffline() {
  const [offline, setOffline] = useState(false);
  useEffect(() => NetInfo.addEventListener(state => {
    setOffline(state.isConnected === false || state.isInternetReachable === false);
  }), []);
  return offline;
}
