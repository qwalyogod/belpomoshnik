import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { useStore } from "../data/store";
import { GuestGuardModal } from "./extra-screens";

/**
 * GuestGuardBridge слушает guestGuardSignal из стора. Когда сигнал
 * инкрементится (любое защищённое действие из гостя), открывает модал
 * с предложением войти или зарегистрироваться.
 *
 * Рендерится один раз внутри <AppStoreProvider>.
 */
export function GuestGuardBridge() {
  const { guestGuardSignal, dismissGuestGuard } = useStore();
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (guestGuardSignal > 0) {
      setOpen(true);
    }
  }, [guestGuardSignal]);

  const close = () => {
    setOpen(false);
    dismissGuestGuard();
  };

  return (
    <GuestGuardModal
      open={open}
      onClose={close}
      onSignIn={() => {
        close();
        navigate("/login");
      }}
      onRegister={() => {
        close();
        navigate("/register");
      }}
    />
  );
}
