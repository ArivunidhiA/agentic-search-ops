import { cn } from '../../lib/utils';
import { BorderTrail } from './border-trail';
import { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  showBorderTrail?: boolean;
  borderTrailSize?: number;
  noPadding?: boolean;
}

export function Card({ 
  children, 
  className, 
  showBorderTrail = true,
  borderTrailSize = 60,
  noPadding = false
}: CardProps) {
  return (
    <div className={cn(
      "relative rounded-lg bg-white shadow overflow-hidden",
      !noPadding && "p-6",
      className
    )}>
      {showBorderTrail && (
        <BorderTrail
          style={{
            boxShadow:
              "0px 0px 60px 30px rgb(255 215 0 / 50%), 0 0 100px 60px rgb(255 215 0 / 30%), 0 0 140px 90px rgb(255 215 0 / 20%)",
          }}
          size={borderTrailSize}
          className="bg-gradient-to-l from-yellow-300 via-yellow-500 to-yellow-300"
        />
      )}
      {children}
    </div>
  );
}
