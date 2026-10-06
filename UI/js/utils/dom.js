export function setBusy(element, busy) {
  element?.querySelectorAll("button, input").forEach((control) => {
    control.disabled = busy;
  });
  element?.classList.toggle("is-busy", busy);
}

export function wait(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

