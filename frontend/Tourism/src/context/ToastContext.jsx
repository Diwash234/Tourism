import { createContext, useState, useCallback } from "react";
import Toast from "../components/common/Toast";


export const ToastContext = createContext(null);


export const ToastProvider = ({ children }) => {

  const [toasts, setToasts] = useState([]);


  const showToast = useCallback(
    (message, type = "info") => {

      const id = Date.now() + Math.random();


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
          top-4
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