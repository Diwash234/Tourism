import { createContext, useState, useCallback, useRef } from "react";
import Toast from "../components/common/Toast";


export const ToastContext = createContext(null);


export const ToastProvider = ({ children }) => {

  const [toasts, setToasts] = useState([]);

  // Suppress identical toasts fired back-to-back (e.g. React StrictMode runs a
  // mount effect twice in dev, which used to show "This workspace is not
  // assigned to you" twice on /staff).
  const lastToast = useRef({ message: null, type: null, at: 0 });

  const showToast = useCallback(
    (message, type = "info") => {
      const now = Date.now();
      if (
        lastToast.current.message === message &&
        lastToast.current.type === type &&
        now - lastToast.current.at < 1500
      ) {
        return;
      }
      lastToast.current = { message, type, at: now };

      const id = now + Math.random();


      setToasts((prev) => [
        ...prev,
        {
          id,
          message,
          type,
        },
      ]);


      setTimeout(() => {

        setToasts((prev) =>
          prev.filter(
            (toast) => toast.id !== id
          )
        );

      }, 3500);

    },
    []
  );



  return (

    <ToastContext.Provider
      value={{
        showToast,
      }}
    >

      {children}


      <div
        className="
          fixed
          top-20
          right-4
          z-[9999]
          space-y-2
        "
      >

        {toasts.map((toast) => (

          <Toast
            key={toast.id}
            message={toast.message}
            type={toast.type}
          />

        ))}

      </div>


    </ToastContext.Provider>

  );

};