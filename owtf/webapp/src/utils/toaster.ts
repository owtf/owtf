import { toast } from "sonner";

function messageText(message: unknown): string {
  if (typeof message === "string") {
    return message;
  }
  try {
    return JSON.stringify(message);
  } catch {
    return String(message);
  }
}

const toaster = {
  success(message: unknown) {
    toast.success(messageText(message));
  },
  danger(message: unknown) {
    toast.error(messageText(message));
  },
  warning(message: unknown) {
    toast.warning(messageText(message));
  },
  notify(message: unknown) {
    toast(messageText(message));
  },
};

export default toaster;
