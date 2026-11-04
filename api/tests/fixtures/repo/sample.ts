import { Logger } from "./logger";

export interface User {
  id: string;
}

export type UserId = string;

export const greet = (user: User): string => {
  return `hi ${user.id}`;
};

export default class Service {
  private log = new Logger();

  async send(payload: string): Promise<void> {
    this.log.info(payload);
  }
}
