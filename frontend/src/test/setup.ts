import "@testing-library/jest-dom/vitest";

Object.defineProperty(URL, "createObjectURL", {
  value: () => "blob:foodsugar-test-preview",
});

class ResizeObserverMock {
  observe() {
    return undefined;
  }

  unobserve() {
    return undefined;
  }

  disconnect() {
    return undefined;
  }
}

Object.defineProperty(globalThis, "ResizeObserver", {
  value: ResizeObserverMock,
});
