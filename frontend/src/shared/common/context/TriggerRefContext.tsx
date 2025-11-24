import {
  createContext,
  ReactNode,
  RefObject,
  useContext,
  useState,
} from "react";

type TriggerRefContextType = {
  triggerRef: RefObject<HTMLButtonElement | null>;
  setTriggerRef: (ref: RefObject<HTMLButtonElement | null>) => void;
};

const TriggerRefContext = createContext<TriggerRefContextType | undefined>(
  undefined,
);

export const useTriggerRef = () => {
  const context = useContext(TriggerRefContext);
  if (!context) {
    throw new Error("useTriggerRef must be used within a TriggerRefProvider");
  }
  return context;
};

export const TriggerRefProvider = ({ children }: { children: ReactNode }) => {
  const [triggerRef, setTriggerRef] = useState<any>(null);

  return (
    <TriggerRefContext.Provider value={{ triggerRef, setTriggerRef }}>
      {children}
    </TriggerRefContext.Provider>
  );
};
