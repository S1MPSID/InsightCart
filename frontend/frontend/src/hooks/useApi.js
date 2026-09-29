import { useCallback, useEffect, useRef, useState } from "react";

const INITIAL = { data: null, loading: true, error: null };

/**
 * Single fetch-and-track hook for every analytics read.
 *
 * Handles the three states the UI always needs (loading, error, data) plus the
 * two things the per-page copy/paste blocks got wrong: a slow response landing
 * after a filter change, and setState after unmount. `reload` backs the retry
 * button on ErrorState.
 */
export default function useApi(loader, deps = []) {
  const [state, setState] = useState(INITIAL);

  const requestId = useRef(0);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  // No state is set before the first await, so mounting never cascades renders.
  const execute = useCallback(async (currentLoader) => {
    const id = ++requestId.current;
    try {
      const result = await currentLoader();
      if (!mounted.current || id !== requestId.current) return;
      setState({ data: result, loading: false, error: null });
    } catch (err) {
      if (!mounted.current || id !== requestId.current) return;
      setState({ data: null, loading: false, error: describeError(err) });
    }
  }, []);

  const reload = useCallback(() => {
    setState((previous) => ({ ...previous, loading: true, error: null }));
    return execute(loader);
  }, [execute, loader]);

  useEffect(() => {
    // `execute` sets state only after its first `await`, so no update happens
    // synchronously during the effect body. The rule cannot see past that
    // async boundary, hence the targeted disable.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    execute(loader);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { ...state, reload };
}

/** Turns an axios/FastAPI failure into a sentence worth showing a user. */
function describeError(err) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string" && detail) return detail;
  if (err?.code === "ERR_NETWORK" || err?.message === "Network Error") {
    return "Cannot reach the analytics API. Confirm the backend is running on port 8000.";
  }
  if (err?.response?.status === 422) return "The API rejected these parameters.";
  return "Something went wrong while loading this data.";
}
